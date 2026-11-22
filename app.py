import logging

import streamlit as st

from chat_flow import process_chat_turn
from config import AppConfig
from llama_cpp_client import LlamaCppClient
from language_validator import (
    ASSAMESE_ONLY_MESSAGE,
    LanguageDetectorError,
    get_language_validator,
)
from ollama_client import (
    ModelNotFoundError,
    OllamaError,
    OllamaTimeoutError,
    OllamaUnavailableError,
)

logger = logging.getLogger(__name__)


st.set_page_config(
    page_title="অসমীয়া AI সহায়ক",
    page_icon="💬",
    layout="centered",
)

try:
    config = AppConfig.from_env()
except ValueError:
    logger.exception("Invalid chatbot configuration")
    st.error("ছেটিংছত সমস্যা হৈছে। অনুগ্ৰহ কৰি পৰিৱেশ ছেটিংছ পৰীক্ষা কৰক।")
    st.stop()

client = LlamaCppClient(config)
with st.spinner("স্থানীয় অসমীয়া ভাষা পৰীক্ষক লোড কৰা হৈছে..."):
    try:
        language_validator = get_language_validator()
        language_detector_available = True
    except LanguageDetectorError:
        language_validator = None
        language_detector_available = False
        logger.exception("Could not load the local Assamese language detector")

if "messages" not in st.session_state:
    st.session_state.messages = []


def clear_conversation() -> None:
    st.session_state.messages = []


st.title("অসমীয়া AI সহায়ক")
st.caption("আপোনাৰ অসমীয়া কথোপকথন স্থানীয় llama.cpp মডেলত চলে।")
st.info("এই সহায়কে কেৱল অসমীয়া লিখনি গ্ৰহণ কৰে আৰু কেৱল অসমীয়াত উত্তৰ দিয়ে।")

with st.sidebar:
    st.subheader("সহায়কৰ বিষয়ে")
    st.write("অসমীয়া ভাষাত প্ৰশ্ন সোধক আৰু স্থানীয় মডেলৰ পৰা উত্তৰ পাওক।")
    if language_detector_available:
        st.success("স্থানীয় অসমীয়া ভাষা পৰীক্ষক সাজু।")
    else:
        st.error("স্থানীয় অসমীয়া ভাষা পৰীক্ষক লোড কৰিব পৰা নগ'ল।")
        st.caption(
            "প্ৰয়োজনীয়তা সংস্থাপন কৰক আৰু IndicLID-ৰ প্ৰথম model download-ৰ বাবে "
            "internet সংযোগ পৰীক্ষা কৰক।"
        )

    try:
        model_is_available = client.model_available()
    except OllamaUnavailableError:
        model_is_available = False
        logger.exception("Could not check the local GGUF inference server")
        st.error("স্থানীয় মডেল সেৱা উপলব্ধ নহয়। chatbot startup ফাইল চলাই পুনৰ চেষ্টা কৰক।")
    except OllamaError:
        model_is_available = False
        logger.exception("Local GGUF inference status check failed")
        st.error("স্থানীয় মডেলৰ অৱস্থা পৰীক্ষা কৰিব পৰা নগ'ল। সেৱাটো পৰীক্ষা কৰক।")
    else:
        if model_is_available:
            st.success("স্থানীয় সহায়ক সাজু।")
        else:
            st.warning("স্থানীয় সহায়ক আৰম্ভ কৰিব পৰা নগ'ল। সংস্থাপন পৰীক্ষা কৰক।")

    st.divider()
    st.subheader("উত্তৰৰ ছেটিংছ")
    temperature = st.slider("সৃষ্টিশীলতা", 0.0, 2.0, config.temperature, 0.1)
    num_predict = st.slider("সৰ্বাধিক উত্তৰ টোকেন", 64, 512, config.num_predict, 32)
    history_messages = st.slider(
        "মনত ৰখা আগৰ বাৰ্তাৰ সংখ্যা",
        0,
        8,
        min(config.history_messages, 8),
    )
    st.caption("কথোপকথন কেৱল এই session-ত থাকে; disk-ত সংৰক্ষণ কৰা নহয়।")

    if st.button("Clear Conversation", use_container_width=True):
        clear_conversation()
        st.rerun()

header_col, new_chat_col = st.columns([5, 1])
with header_col:
    st.subheader("কথোপকথন")
with new_chat_col:
    if st.button("New Chat", use_container_width=True):
        clear_conversation()
        st.rerun()

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message.get("complete") is False:
            st.warning("এই উত্তৰটো অসম্পূৰ্ণ হ'ব পাৰে। প্ৰয়োজন হ'লে পুনৰ সুধক বা সৰ্বাধিক টোকেন বঢ়াওক।")

prompt = st.chat_input(
    "ইয়াত কেৱল অসমীয়াত প্ৰশ্ন লিখক...",
    disabled=not model_is_available or not language_detector_available,
)

if prompt:
    if not language_validator:
        st.error("স্থানীয় অসমীয়া ভাষা পৰীক্ষক উপলব্ধ নহয়।")
    else:
        with st.spinner("ভাষা পৰীক্ষা কৰি উত্তৰ প্ৰস্তুত কৰা হৈছে..."):
            try:
                result = process_chat_turn(
                    prompt,
                    st.session_state.messages,
                    language_validator,
                    client,
                    temperature=temperature,
                    num_predict=num_predict,
                    history_messages=history_messages,
                )
            except LanguageDetectorError:
                logger.exception("Local Assamese language identification failed")
                st.error("স্থানীয় ভাষা পৰীক্ষা কৰিব পৰা নগ'ল। setup-ৰ নিৰ্দেশনা অনুসৰণ কৰক।")
            except ModelNotFoundError:
                logger.exception("The configured local GGUF model is missing")
                st.error("স্থানীয় মডেল লোড হোৱা নাই। model file আৰু llama.cpp runtime পৰীক্ষা কৰক।")
            except OllamaUnavailableError:
                logger.exception("The local llama.cpp server is unavailable")
                st.error("স্থানীয় মডেল সেৱা উপলব্ধ নহয়। startup-ত দেখুওৱা ত্ৰুটি পৰীক্ষা কৰক।")
            except OllamaTimeoutError:
                logger.exception("The local GGUF generation request timed out")
                st.error("উত্তৰ প্ৰস্তুত কৰিবলৈ অধিক সময় লাগিল। সৰু context বা কম উত্তৰ টোকেন চেষ্টা কৰক।")
            except OllamaError:
                logger.exception("The local GGUF model request failed")
                st.error("স্থানীয় মডেলৰ পৰা উত্তৰ পোৱা নগ'ল। llama.cpp server log পৰীক্ষা কৰক।")
            else:
                if result.status == "input_rejected":
                    st.warning(ASSAMESE_ONLY_MESSAGE)
                elif result.status == "output_rejected":
                    st.warning(result.message)
                elif result.status == "incomplete":
                    st.warning(result.message)
                elif result.status == "accepted":
                    with st.chat_message("user"):
                        st.markdown(prompt.strip())
                    with st.chat_message("assistant"):
                        st.markdown(result.response)
