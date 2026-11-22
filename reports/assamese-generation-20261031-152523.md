# Assamese Generation Quality Experiment

- Run time: 2026-10-31T15:15:09+05:30
- Model: `trubits/kakugo-3b-asm:q4_k_m`
- Ollama version: `0.40.13`
- Production files/settings changed: **No**
- Requests: direct, local `/api/chat`; each trial starts with the same system prompt and one user prompt.
- `think: false`; responses are recorded verbatim, including any visible thinking tags.

## Model and request inspection

- Installed model template: TEMPLATE {{ .Prompt }}; stop tokens: <|start_of_role|>, <|end_of_role|>, <|end_of_text|> (from `ollama show --modelfile`)
- Installed model parameters: No temperature/top_p/repeat_penalty/num_predict declarations (from `ollama show --parameters`)
- The installed model template is `{{ .Prompt }}` with the stop tokens listed above; `/api/chat` receives structured role/content messages and Ollama formats them for the model.
- The installed Modelfile did not declare `temperature`, `top_p`, `repeat_penalty`, or `num_predict`; baseline values come from the production request and the rest use Ollama defaults.
- Ollama's API spelling for repetition penalty is `repeat_penalty`.
- `think: false` did not prevent visible `<think>` blocks in 27/30 raw responses.
- Ollama reported `done_reason='length'` for 4/30 responses; `done=True` can still accompany this limit reason.

## Configuration comparison

| ID | Options changed from baseline | Exact request options |
|---|---|---|
| `production_baseline` | `{"(none)": "(baseline)"}` | `{"temperature": 0.7, "num_predict": 1024}` |
| `lower_temperature` | `{"temperature": 0.3}` | `{"temperature": 0.3, "num_predict": 1024}` |
| `lower_top_p` | `{"top_p": 0.75}` | `{"temperature": 0.7, "num_predict": 1024, "top_p": 0.75}` |
| `higher_repeat_penalty` | `{"repeat_penalty": 1.2}` | `{"temperature": 0.7, "num_predict": 1024, "repeat_penalty": 1.2}` |
| `larger_output_limit` | `{"num_predict": 1536}` | `{"temperature": 0.7, "num_predict": 1536}` |

## Results and qualitative comparison

Ratings below are manual observational judgments of these individual generations, not benchmark scores. Fluency, grammar, factual correctness, and instruction following use 1 (poor) to 5 (strong); repetition uses 1 (little/no repetition) to 5 (severe repetition). The factual ratings are a practical review, not subject-matter expert certification. They do not establish that one setting is generally better.

### cpu

Prompt: CPU কি? সহজ অসমীয়াত বুজাই দিয়ক।

| Configuration | Fluency | Grammar | Factual correctness | Repetition | Instruction following | Latency (s) | Completion | Notes |
|---|---:|---:|---:|---:|---:|---:|---|---|
| Production-like baseline | 1/5 | 1/5 | 1/5 | 1/5 | 2/5 | 20.369 | done=True, reason='stop' | Awkward terminology and inaccurate CPU description; think text leaked. |
| Temperature 0.3 | 3/5 | 3/5 | 4/5 | 1/5 | 4/5 | 7.63 | done=True, reason='stop' | Most understandable CPU explanation in this set; still has awkward wording and think text. |
| top_p 0.75 | 1/5 | 1/5 | 1/5 | 2/5 | 2/5 | 10.756 | done=True, reason='stop' | Invented/incorrect terminology and repeated definition; think text leaked. |
| repeat_penalty 1.2 | 1/5 | 1/5 | 1/5 | 1/5 | 1/5 | 14.679 | done=True, reason='stop' | Final answer is largely Odia/English-script text, not usable Assamese. |
| num_predict 1536 | 1/5 | 1/5 | 1/5 | 1/5 | 2/5 | 11.63 | done=True, reason='stop' | Several technical claims/phrases are confused; think text leaked. |

#### Production-like baseline

- Request options: `{"temperature": 0.7, "num_predict": 1024}`
- Response time: 20.369 seconds
- Completion: `done=True`, `done_reason='stop'`
- Token/timing metadata: `{"prompt_eval_count": 208, "eval_count": 237, "total_duration_ns": 20341463800, "load_duration_ns": 10965150300, "prompt_eval_duration_ns": 1529785000, "eval_duration_ns": 7804274000}`

Exact model response:

````text
<think> We need to explain CPU in simple Assamese, short. No markdown. </think> CPU মানে “কেন্দ্ৰীয় গণনা এলেকা” (Central Processing Unit)। ইয়াই কম্পিউটাৰৰ মূল মডেল, যি সকলো তথ্য আৰু কোড পঢ়ি, তেজস্বী কৰি, ফলাফল দিয়ে। একেবাৰে চাবি বা মূখ্য গেমিং প্ৰসেসৰ হিচাপে কাম কৰে।
````

#### Temperature 0.3

- Request options: `{"temperature": 0.3, "num_predict": 1024}`
- Response time: 7.63 seconds
- Completion: `done=True`, `done_reason='stop'`
- Token/timing metadata: `{"prompt_eval_count": 208, "eval_count": 229, "total_duration_ns": 7625368700, "load_duration_ns": 24107800, "prompt_eval_duration_ns": 36034000, "eval_duration_ns": 7414216000}`

Exact model response:

````text
<think> We need to answer in Assamese, simple, short. Explain CPU. Provide simple explanation. </think> CPU মানে কম্পিউটাৰৰ মূল মগজু। ই তথ্য পঢ়ে, গণনা কৰে আৰু কম্পিউটাৰৰ অন্য অংশসমূহক কাম কৰাবলৈ আদেশ দিয়ে। সংক্ষেপে, CPU হৈছে কম্পিউটাৰৰ মূল কাৰ্যক্ষমতা কেন্দ্ৰ।
````

#### top_p 0.75

- Request options: `{"temperature": 0.7, "num_predict": 1024, "top_p": 0.75}`
- Response time: 10.756 seconds
- Completion: `done=True`, `done_reason='stop'`
- Token/timing metadata: `{"prompt_eval_count": 208, "eval_count": 335, "total_duration_ns": 10750462500, "load_duration_ns": 29482300, "prompt_eval_duration_ns": 31995000, "eval_duration_ns": 10456604000}`

Exact model response:

````text
<think> We need to explain CPU in simple Assamese. Keep short. No markdown. </think> CPU মানে কেন্দ্রীয় প্ৰসেসিং ইউনিট। ই কম্পিউটাৰৰ মূল মাইক্ৰো‑কম্পিউটাৰৰ মানে, যি তথ্য আৰু আদেশ পঢ়ি, তেওঁলোকক সঠিকভাৱে প্ৰসেস কৰে। এইদৰে কম্পিউটাৰ কাম চলায়। সংক্ষেপে ক'বলৈ গ'লে, CPU হৈছে কম্পিউটাৰৰ মূল মাইক্ৰো‑কম্পিউটাৰ যি সকলো কাম শেষ কৰে।
````

#### repeat_penalty 1.2

- Request options: `{"temperature": 0.7, "num_predict": 1024, "repeat_penalty": 1.2}`
- Response time: 14.679 seconds
- Completion: `done=True`, `done_reason='stop'`
- Token/timing metadata: `{"prompt_eval_count": 208, "eval_count": 408, "total_duration_ns": 14672261000, "load_duration_ns": 23057900, "prompt_eval_duration_ns": 35115000, "eval_duration_ns": 14412194000}`

Exact model response:

````text
<think> The user asks in Assamese: "What is CPU? Explain simply. In simple Assamese." Need to answer concisely, minimal formatting.

We need short but clear explanation of Central Processing Unit (CPU). Use plain text with no markdown or lists ideally just one paragraph maybe separated by commas. No URLs.

Let's produce a concise response in Assamese: "কেন্দ্ৰীয প্ৰসেছিং ইউনিট (CPU) হ'ল মাচিনৰা এখনি, য'ত বগাক-ডাঙ্গী অপাৰেশন সমাধান কৰে; ইটো ছিষ্টেমৰ হৃদ্‌য়।"

But need to be simple. Could say: "CPU = CPU, অর্থাৎ 'Central Processing Unit' – কম্পিউটাৰত ৰাইচি (ଡেট) হ'ল।"

We'll give a short answer: "CPU সংখ্যানুষ্ঠান, CPU = Central Processing Unit – ୟনସିକ୍‌ (Central), ପ্ରସେସ)।"

Ok. </think> সেং‑ମା’ – CPU =  Central Processing Unit, i.e., ‘ହୃଦ୍‌ କଣି’.
````

#### num_predict 1536

- Request options: `{"temperature": 0.7, "num_predict": 1536}`
- Response time: 11.63 seconds
- Completion: `done=True`, `done_reason='stop'`
- Token/timing metadata: `{"prompt_eval_count": 208, "eval_count": 343, "total_duration_ns": 11625868500, "load_duration_ns": 28105300, "prompt_eval_duration_ns": 425564000, "eval_duration_ns": 11095478000}`

Exact model response:

````text
<think> We need to answer in Assamese, simple conversational tone, minimal formatting. Explain CPU. Provide simple explanation. Ensure short. </think> CPU মানে কেইবাটাও প্রসেসর কেন্দ্ৰ। ই কম্পিউটাৰক কোড, ফাংশন, ডাটা ইত্যাদি মানবুকিক (কোড) পঢ়ি, তেখেতক এক একেটা ক্লাক (ছাপ)ত কাম কৰে। সকলোতে যিটো কাম শেষ হয়, তাতে ফলাফল বা তথ্য অন্য প্ৰসেসৰলৈ পঠাই দিয়া হয়। সুতরাং CPU হৈছে কম্পিউটাৰৰ মূল কামকাৰী যন্ত্র।
````

### photosynthesis

Prompt: অষ্টম শ্ৰেণীৰ ছাত্ৰ-ছাত্ৰীৰ বাবে সালোক-সংশ্লেষণ অসমীয়াত বুজাই দিয়ক।

| Configuration | Fluency | Grammar | Factual correctness | Repetition | Instruction following | Latency (s) | Completion | Notes |
|---|---:|---:|---:|---:|---:|---:|---|---|
| Production-like baseline | 2/5 | 2/5 | 1/5 | 1/5 | 1/5 | 22.817 | done=True, reason='stop' | Explains sunlight/heat, not photosynthesis; key request misunderstood. |
| Temperature 0.3 | 2/5 | 2/5 | 1/5 | 1/5 | 1/5 | 18.572 | done=True, reason='stop' | Defines a grammatical concept instead of photosynthesis. |
| top_p 0.75 | 1/5 | 1/5 | 1/5 | 5/5 | 1/5 | 34.388 | done=True, reason='length' | Repeats uncertainty about the term until num_predict truncation. |
| repeat_penalty 1.2 | 2/5 | 2/5 | 1/5 | 1/5 | 1/5 | 30.543 | done=True, reason='stop' | Switches to light interactions/reflection/refraction rather than photosynthesis. |
| num_predict 1536 | 1/5 | 1/5 | 1/5 | 1/5 | 1/5 | 37.242 | done=True, reason='stop' | Answers about the solar system; the topic is wrong despite normal stop. |

#### Production-like baseline

- Request options: `{"temperature": 0.7, "num_predict": 1024}`
- Response time: 22.817 seconds
- Completion: `done=True`, `done_reason='stop'`
- Token/timing metadata: `{"prompt_eval_count": 263, "eval_count": 724, "total_duration_ns": 22809850400, "load_duration_ns": 23871800, "prompt_eval_duration_ns": 694869000, "eval_duration_ns": 22029476000}`

Exact model response:

````text
<think> The user asks in Assamese: "Explain sunlight and interaction in Assamese for 8th grade students." Need to explain concepts of sunlight and interaction in Assamese, simple conversational tone, short as possible, minimal formatting. Provide definitions, maybe diagram description. Use Assamese. No markdown. Keep short. </think> সালোক (সূর্যকিৰণ) হৈছে সূৰ্যকেন্দ্ৰিক আলোকশক্তি। সূৰ্যালোকে পৃথিৱীলৈ আহি তাপ, উষ্ণতা, আদিৰে সমগ্ৰ জগতক উষ্ণ কৰে।  

সালোক পৃষ্ঠত যিকোনো বস্তু (যেনে পত্র, জল) তলত বা উপৰিত লৈ যায়, তেতিয়া সেই বস্তুই সোনকালেই উষ্ণতা অনুভৱ কৰে। যদি বস্তু সালোকৰ কণি মাটিত পৰা বুলি ধৰা যায়, তেন্তে তাতে শক্তি আৰু তাপ পোৱা যায়। ইমানেই নহয়, সালোক বস্তুৰ উপৰত থকা ছাঁদ বা বাতাসৰ সৈতে মিলি গৰম পাতা বা গরম জল প্ৰস্তুত কৰে। সেয়ে, সালোক হ’ল আমাৰ দৈনন্দিন জীৱনৰ এক অতি প্ৰয়োজনীয় শক্তি, যি আমাৰ জীৱনক সজীৱ আৰু উষ্ণ কৰি তুলে।
````

#### Temperature 0.3

- Request options: `{"temperature": 0.3, "num_predict": 1024}`
- Response time: 18.572 seconds
- Completion: `done=True`, `done_reason='stop'`
- Token/timing metadata: `{"prompt_eval_count": 263, "eval_count": 559, "total_duration_ns": 18568404400, "load_duration_ns": 24732900, "prompt_eval_duration_ns": 691990000, "eval_duration_ns": 17775680000}`

Exact model response:

````text
<think> The user asks: "অষ্টম শ্ৰেণীৰ ছাত্ৰ-ছাত্ৰীৰ বাবে সালোক-সংশ্লেষণ অসমীয়াত বুজাই দিয়ক।" They want explanation of "সালোক-সংশ্লেষণ" in Assamese for 8th grade students. Need to give simple explanation, in Assamese, short, conversational. No markdown. Provide correct info. </think> সালোক-সংশ্লেষণ মানে হৈছে দুটা বা ততোধিক শব্দ বা বাক্য একে সময়তে একে অন্যক সংযোগ কৰি একত্ৰে কাম কৰা। উদাহৰণস্বৰূপে, “মই গছটোক গছলৈ লৈ গলোঁ” বুলিলে “গছটো” আৰু “গছলৈ” দুটা শব্দে একে অন্যক সংযোগ কৰি কাম কৰিছে। সেয়ে, সালোক-সংশ্লেষণ হৈছে শব্দবোৰ একে সময়তে একে অন্যক সংযোগ কৰি একত্ৰে কাম কৰা।
````

#### top_p 0.75

- Request options: `{"temperature": 0.7, "num_predict": 1024, "top_p": 0.75}`
- Response time: 34.388 seconds
- Completion: `done=True`, `done_reason='length'`
- Token/timing metadata: `{"prompt_eval_count": 263, "eval_count": 1024, "total_duration_ns": 34383903700, "load_duration_ns": 30428900, "prompt_eval_duration_ns": 35490000, "eval_duration_ns": 34136629999}`

Exact model response:

````text
<think> User asks: "Explain light-conversation in Assamese for 8th grade students." They want explanation of light-conversation (maybe "সালোক-সংশ্লেষণ"?) Probably they mean "সালোক-সংশ্লেষণ" meaning "সালোক-সংশ্লেষণ"? Could be "সালোক-সংশ্লেষণ" meaning "সালোক-সংশ্লেষণ" maybe "সালোক-সংশ্লেষণ" refers to "সালোক-সংশ্লেষণ" in physics? Not sure. Might be "সালোক-সংশ্লেষণ" meaning "সালোক-সংশ্লেষণ" maybe "সালোক-সংশ্লেষণ" = "সালোক-সংশ্লেষণ" is a term used in physics for "সালোক-সংশ্লেষণ" meaning "সালোক-সংশ্লেষণ"?? Could be "সালোক-সংশ্লেষণ" meaning "সালোক-সংশ্লেষণ" = "সালোক-সংশ্লেষণ"?? Might be "সালোক-সংশ্লেষণ" meaning "সালোক-সংশ্লেষণ" = "সালোক-সংশ্লেষণ"?? Could be "সালোক-সংশ্লেষণ" meaning "সালোক-সংশ্লেষণ"?? I'm not sure. Maybe they refer to "সালোক-সংশ্লেষণ" as "সালোক-সংশ্লেষণ" = "সালোক-সংশ্লেষণ"?? Actually "সালোক-সংশ্লেষণ" could be "সালোক-সংশ্লেষণ" meaning "সালোক-সংশ্লেষণ"?? I'm not sure. Maybe they mean "সালোক-সংশ্লেষণ" as "সালোক-সংশ্লেষণ" meaning "সালোক-সংশ্লেষণ"?? Could be "সালোক-সংশ্লেষণ" meaning "সালোক-সংশ্লেষণ"?? I'm not sure.

Maybe they refer to "সালোক-সংশ্লেষণ" meaning "সালোক-সংশ্লেষণ"?? I think they mean "সালোক-সংশ্লেষণ" meaning "সালোক-সংশ্লেষণ"?? Could be "সালোক-সংশ্লেষণ" meaning "সালোক
````

#### repeat_penalty 1.2

- Request options: `{"temperature": 0.7, "num_predict": 1024, "repeat_penalty": 1.2}`
- Response time: 30.543 seconds
- Completion: `done=True`, `done_reason='stop'`
- Token/timing metadata: `{"prompt_eval_count": 263, "eval_count": 827, "total_duration_ns": 30530877400, "load_duration_ns": 39387400, "prompt_eval_duration_ns": 34656000, "eval_duration_ns": 30194102000}`

Exact model response:

````text
<think> User asks: "Explain sunlight interaction in Assamese for 8th grade students." Provide simple, clear explanation of how light interacts with objects (reflection, refraction). Keep short. Use conversational tone.

We must not use markdown formatting; keep minimal lines. Probably a paragraph or two sentences per concept then summary.

Will give examples: white sunlight splits into colors when passes through prism? For reflection, plane mirror gives image same size reversed left-right etc. Refract via convex lens bending rays towards eye.

Make short but clear enough for 8th graders. Use Assamese script.

Let's craft answer in plain text with line breaks maybe simple sentences separated by commas or periods; no markdown list? Could use bullet points like "সাদা আলো" etc, it is okay as long not too formal formatting. Avoid excessive punctuation but we can have short lines for each concept.

Will keep answer concise ~150 words total. </think> ধন্যবাদ! এইটি সান‑শিকাৰ (sunlight) - প্ৰেজেন্ট‑ফল, রেণ্ড, নমনীয়‑বদ্ধি ইত্যাদিক “সংশ্লেষ” (Interaction) হ'ব।  

**1. ৰিফ্‌লেচন (reflection)**  
- আলো‑পাৱনি ‘mirror’ কাটি, ୧° (നേ) ദിശത “image” രൂപമാണ്।  
- ছবিখে‌না (reflection angle = incident angle).  

**2. ৰেଫ্ৰ্যাকশ্যন (refraction)**  
- ସමු (transparent) ‘water’ অ'ണ്ട് ‘glass lens’‑এ ছাৱি, 
  - glass (convex/curved) → light rays bend towards normal.  
- ಇದು “focus” ആൻഡ് “eye‑seeing”.  

**3. ପ୍ରସାর (illumination)**  
- সাধাৰণ (white) sunlight → white light, 
  - prism or goggle lens দ্বারা “rainbow”‑এ color separation.  

**4. ସୁന്തർ‌(absorption)**  
- কিছু material (colorful glass) → absorption, no reflection; sun’s colors disappear as black.

সেই धरनेৰে sunlight‑এর different interactions—reflection দ্বারা “image” formation, refraction তে “bending”, prism‑তে rainbow।  

আনুমানিক 8th grade class‑room:  
- reflection = mirror (same size), 
- refractive index ≈1.5 for glass lens, 

এই ধাৰণাবোৰে sunlight‑ক “image” আর “rainbow” ৰূপে দেখিছে।  

Hope that helps!
````

#### num_predict 1536

- Request options: `{"temperature": 0.7, "num_predict": 1536}`
- Response time: 37.242 seconds
- Completion: `done=True`, `done_reason='stop'`
- Token/timing metadata: `{"prompt_eval_count": 263, "eval_count": 1014, "total_duration_ns": 37234539500, "load_duration_ns": 17894700, "prompt_eval_duration_ns": 697791000, "eval_duration_ns": 36420101000}`

Exact model response:

````text
<think> User asks: "অষ্টম শ্ৰেণীৰ ছাত্ৰ-ছাত্ৰীৰ বাবে সালোক-সংশ্লেষণ অসমীয়াত বুজাই দিয়ক।" Means: Explain solar system to 8th grade students in Assamese. Need simple, conversational, short but covering basics. Should be minimal formatting, no markdown. Provide brief explanation. </think> সূৰ্য, গ্রহ, দুৰ্গা, দূৰ্গা আদি—সবেকে একে আনক বাহিৰে ঘূৰি থাকে। সূৰ্য হৈছে সেই তীব্ৰ কেন্দ্ৰ, য’ত আলোক, শক্তি আৰু তাপ উৎপন্ন হয়। আমাৰ গ্ৰহ—পৃথিৱী, মেকমাক, বৃহস্পতি, শনি—সূৰ্যক চাৰিওদিশে ঘূৰি থাকে। গ্ৰহবোৰে একে আনক চাৰিওদিশে ঘূৰি থাকে কিন্তু তেওঁলোকৰ ঘূৰণিৰ গতি আৰু দূৰত্ব ভিন্ন। কেতিয়াবা কোনো গ্ৰহ অন্যক ধৰি থাকে (যেনেম গ্ৰহ শনি সূৰ্যক ঘূৰি থাকে) অথবা তীক্ষ্ণ পথে সমান্তৰালভাৱে গতি কৰে। তলত ব্যাস আৰু গতিৰ তফাৎ থাকে—যদি পথবোৰ সমান্তৰাল হয় তেন্তে তফাৎ কম হয়। সেয়া মানে সূৰ্যৰ কেন্দ্ৰত গ্ৰহবোৰ আকাশত দেখা যায়, আৰু সেয়া একে আনক চাৰিওদিশে ঘূৰি থাকে। সারাংশত, সূৰ্য হ’ল কেন্দ্ৰ, গ্ৰহবোৰ সেই কেন্দ্ৰৰ চাৰিওদিশে ঘূৰি থাকে, আৰু তেওঁলোকৰ ঘূৰণি আৰু দূৰত্ব বেলেগ বেলেগ।
````

### assam_sentences

Prompt: অসমৰ বিষয়ে পাঁচটা স্বাভাৱিক অসমীয়া বাক্য লিখক।

| Configuration | Fluency | Grammar | Factual correctness | Repetition | Instruction following | Latency (s) | Completion | Notes |
|---|---:|---:|---:|---:|---:|---:|---|---|
| Production-like baseline | 2/5 | 2/5 | 2/5 | 1/5 | 3/5 | 14.193 | done=True, reason='stop' | Produces five numbered lines, but several are unnatural or semantically odd. |
| Temperature 0.3 | 2/5 | 2/5 | 2/5 | 5/5 | 2/5 | 16.356 | done=True, reason='stop' | Repeats near-identical claims about a rich language/culture. |
| top_p 0.75 | 1/5 | 1/5 | 1/5 | 1/5 | 3/5 | 8.029 | done=True, reason='stop' | Five lines are present but largely nonsensical. |
| repeat_penalty 1.2 | 1/5 | 1/5 | 1/5 | 1/5 | 1/5 | 35.947 | done=True, reason='stop' | Long English planning text and English final sentences; severe instruction failure. |
| num_predict 1536 | 2/5 | 2/5 | 2/5 | 1/5 | 3/5 | 17.945 | done=True, reason='stop' | Five lines are present; wording and some claims are unnatural/questionable. |

#### Production-like baseline

- Request options: `{"temperature": 0.7, "num_predict": 1024}`
- Response time: 14.193 seconds
- Completion: `done=True`, `done_reason='stop'`
- Token/timing metadata: `{"prompt_eval_count": 228, "eval_count": 417, "total_duration_ns": 14187230000, "load_duration_ns": 23449600, "prompt_eval_duration_ns": 487717000, "eval_duration_ns": 13589068000}`

Exact model response:

````text
1. অসমীয়া বংশধৰসকলে বহু সংস্কৃতি আৰু ঐতিহ্যৰে সমৃদ্ধ।
2. অসমৰ মূল ধৰণ হৈছে বজাৰ আৰু বাণিজ্যিক কেন্দ্ৰ।
3. অসমৰ সমৃদ্ধ প্ৰাকৃতিক সম্পদসমূহত অতিৰিক্ত বৰ্ণনা যোগ কৰা নহয়।
4. মধুৰ পৰিবেশ আৰু সমৃদ্ধ জলবায়ুৰ বাবে অসমক বহু বাসিন্দা আকৰ্ষণীয় কৰি তোলে।
5. অসমীয়া সমাজত শৈল্পিক ক্ষেত্ৰসমূহে সমৃদ্ধি আনিছে।
````

#### Temperature 0.3

- Request options: `{"temperature": 0.3, "num_predict": 1024}`
- Response time: 16.356 seconds
- Completion: `done=True`, `done_reason='stop'`
- Token/timing metadata: `{"prompt_eval_count": 228, "eval_count": 509, "total_duration_ns": 16352869700, "load_duration_ns": 23653100, "prompt_eval_duration_ns": 46597000, "eval_duration_ns": 16042401000}`

Exact model response:

````text
অসমীয়া এটা সমৃদ্ধ ভাষা, যি এক সুস্পষ্ট সংস্কৃতি আৰু সমৃদ্ধ ইতিহাসৰ লগত জড়িত। ই এক অতীত যি বহু শতাব্দীৰ পৰা বিকাশ পাইছে, যি এক সমৃদ্ধ ভাষা আৰু সংস্কৃতিৰ প্ৰতিফলন। ই এখন সমৃদ্ধ ভাষা, যি এক সমৃদ্ধ সংস্কৃতি আৰু সমৃদ্ধ ইতিহাসৰ লগত জড়িত। ই এখন সমৃদ্ধ ভাষা, যি এক সমৃদ্ধ সংস্কৃতি আৰু সমৃদ্ধ ইতিহাসৰ লগত জড়িত। ই এখন সমৃদ্ধ ভাষা, যি এক সমৃদ্ধ সংস্কৃতি আৰু সমৃদ্ধ ইতিহাসৰ লগত জড়িত।
````

#### top_p 0.75

- Request options: `{"temperature": 0.7, "num_predict": 1024, "top_p": 0.75}`
- Response time: 8.029 seconds
- Completion: `done=True`, `done_reason='stop'`
- Token/timing metadata: `{"prompt_eval_count": 228, "eval_count": 212, "total_duration_ns": 8025564900, "load_duration_ns": 26777600, "prompt_eval_duration_ns": 40569000, "eval_duration_ns": 7711130000}`

Exact model response:

````text
অসমৰ জলপাতে সুৰভি ভৰা আছে।
বিহু নাচত তেজপাতি গাঁথি বগা হয়।
অসমীয়া পাটল গুঁই বেলি হ'ব।
বহুতো গাঁথি গুলিয়াই পাহি থাকে।
অসমৰ বৰফকোঁৱৰ গাঁথি সলনি হয়।
````

#### repeat_penalty 1.2

- Request options: `{"temperature": 0.7, "num_predict": 1024, "repeat_penalty": 1.2}`
- Response time: 35.947 seconds
- Completion: `done=True`, `done_reason='stop'`
- Token/timing metadata: `{"prompt_eval_count": 228, "eval_count": 945, "total_duration_ns": 35943211400, "load_duration_ns": 18139000, "prompt_eval_duration_ns": 41902000, "eval_duration_ns": 35678885000}`

Exact model response:

````text
<think> We need to write five natural Assamese sentences about Assam. Minimal formatting, simple tone.

Provide list maybe separated by line breaks but minimal.

Let's do:

1. ... 2... etc

Ok produce short lines each sentence in Assamese describing something typical of Assam: tea garden, silk weaving, bamboo products, river Brahmaputra, cultural festivals like Bihu.

Will output as plain text with newlines or maybe dash-separated sentences? The instruction says minimal formatting; can use line breaks. Provide five natural Assamese statements about Assam. Let's do:

- অসামীয়ানি ভিজে থাকে, তাপ্লা (the tea) ।

Better: "Assam is known for its rich biodiversity and scenic landscapes."

But need five natural Assamese sentences about the state of Assam.

Will produce:

1. অসীমি ব্‌রহ্মাণ্ডে, পিকনিক-শৈলী দৃষ্টিভংগি।

Let's craft.

Make sure each is a complete sentence in Assamese. Provide five sentences separated by line breaks maybe with numbers? Could be just list of lines numbered 1 to5, but that might count as formatting; we can still do simple numbering without markdown heavy tags (just plain text).

Ok produce:

১) অসামী গাছে লতা-নির্ভিদ্য ব্‌টোক।

But better: "Assam's tea gardens are famous for their lush greenery."

Let's write:

1. Assamese tea is renowned across the world.

2. The Sualkuchi silk industry is a major contributor to handloom products in Assam...

Need five sentences, each describing something typical of Assam (tea garden landscape). Provide as short but complete sentences.

Ok produce: 

১) অসামীনি চা-গ্‌রামে লতা‑প্রিয়া ৰঙান।

But that's not natural Assamese. Let's write:

1. বৌদ্ধভুনি, আহক! (Maybe too literal.)

Probably better: "Assam is the birthplace of many festivals like Bihu and Durga Puja."

Ok produce list.

Let me craft 5 sentences in Assamese:

1. অসাম্যাৰ প্ৰধান শিল্প, চা‑গাছের বন।

2. হিংদি-ভিজা ৰ‍্হীসা (maybe not).

Actually let's do:

1. Assam is known for its rich tea gardens and scenic beauty.

But we need natural sentences, maybe about daily life: "Assamese people enjoy the cool breeze of Brahmaputra."

Ok produce five concise statements in Assamese describing general things you can say while talking about Assam.

Let's write:

1. অসাম্যাৰ নিল‑নির্দেশ হ'ব, ৰ’ণ্‌গা।

Hmm not clear.

Ok final answer in plain text with line breaks and numbers for reference but minimal formatting. Provide five sentences about Assam:

1. অসাম্যায়িক নন‑ফেইরি (maybe).

I'll just produce a simple list of statements, each on separate lines.

 </think> - Assamese tea gardens are famous for their lush greenery and fresh aroma।  
- Brahmaputra River is the lifeline of Assam's agriculture.  
- Sualkuchi silk weavers create exquisite handloom products in this region.  
- The traditional Bihu festival brings joy to every household during springtime.  
- Assamese cuisine, with dishes like pitha and laru, reflects the state’s rich cultural heritage.
````

#### num_predict 1536

- Request options: `{"temperature": 0.7, "num_predict": 1536}`
- Response time: 17.945 seconds
- Completion: `done=True`, `done_reason='stop'`
- Token/timing metadata: `{"prompt_eval_count": 228, "eval_count": 484, "total_duration_ns": 17934001000, "load_duration_ns": 33841000, "prompt_eval_duration_ns": 487017000, "eval_duration_ns": 17265785000}`

Exact model response:

````text
<think> We need to produce five natural Assamese sentences about Assam. Keep short. No markdown. Simple. </think> ১. অসমৰ বাটত পুৱা সূৰ্যৰ আলোত হাঁহি সঁচা দৰিদ্ৰ গাঁৱৰ দৃশ্য দেখা যায়।  
২. মণিপুৰী গাঁওত বাটলীয়া মূৰত গছ-গছনি উজ্জ্বল কৰি জীৱনক সজীৱ কৰে।  
৩. গুৱাহাটীৰ সঁচা মেজাজ সকলোৰে মুখত মুখত মিষ্টি হাঁহি দেখা যায়।  
৪. বিহু উৎসৱত মধুৰ গান, নাচ আৰু খাবাৰৰ মিলন দেখা যায়।  
৫. ব্ৰহ্মপুত্ৰ নদী দুয়োফালে পূৰ্ণ কৃষি পালন আৰু কৃষকসকলৰ সমৃদ্ধি দেখা যায়।
````

### artificial_intelligence

Prompt: কৃত্ৰিম বুদ্ধিমত্তা কি? সহজ অসমীয়াত বুজাই দিয়ক।

| Configuration | Fluency | Grammar | Factual correctness | Repetition | Instruction following | Latency (s) | Completion | Notes |
|---|---:|---:|---:|---:|---:|---:|---|---|
| Production-like baseline | 2/5 | 2/5 | 3/5 | 1/5 | 3/5 | 13.779 | done=True, reason='stop' | Broad idea is recognizable, but wording is awkward and anthropomorphic. |
| Temperature 0.3 | 3/5 | 3/5 | 3/5 | 1/5 | 3/5 | 13.57 | done=True, reason='stop' | Understandable broad definition; English think text remains exposed. |
| top_p 0.75 | 3/5 | 3/5 | 3/5 | 1/5 | 3/5 | 14.906 | done=True, reason='stop' | Broadly relevant definition; awkward terminology and visible English think text. |
| repeat_penalty 1.2 | 1/5 | 1/5 | 1/5 | 2/5 | 1/5 | 13.57 | done=True, reason='stop' | Mixed-language, malformed response with unclear claims. |
| num_predict 1536 | 3/5 | 3/5 | 3/5 | 1/5 | 3/5 | 11.927 | done=True, reason='stop' | Relevant short explanation, though it overstates human-like thinking. |

#### Production-like baseline

- Request options: `{"temperature": 0.7, "num_predict": 1024}`
- Response time: 13.779 seconds
- Completion: `done=True`, `done_reason='stop'`
- Token/timing metadata: `{"prompt_eval_count": 233, "eval_count": 416, "total_duration_ns": 13771740000, "load_duration_ns": 28775300, "prompt_eval_duration_ns": 507657000, "eval_duration_ns": 13130411000}`

Exact model response:

````text
<think> We need to respond in Assamese, simple, short, explain AI. No markdown. </think> কৃত্ৰিম বুদ্ধিমত্তা (AI) মানে হ'ল যন্ত্ৰ বা কম্পিউটাৰে মানুহৰ যেন্ত্ৰিক কৌশল, বিচাৰ, বুজা আদি কামবোৰ কৰিব পাৰে। সেই যন্ত্ৰবোৰে ডাটা, সমীকৰণ আৰু নিজৰ অভিজ্ঞতা আধাৰত শিকি, তেনেহলে নতুন সমস্যাত সঠিক সমাধান বা সিদ্ধান্ত দিব পাৰে। সংক্ষেপে, কৃত্ৰিম বুদ্ধিমত্তা হ'ল যন্ত্ৰৰ মানুহৰ মতো বুজাবলৈ আৰু কাম কৰিবলৈ ক্ষমতা।
````

#### Temperature 0.3

- Request options: `{"temperature": 0.3, "num_predict": 1024}`
- Response time: 13.57 seconds
- Completion: `done=True`, `done_reason='stop'`
- Token/timing metadata: `{"prompt_eval_count": 233, "eval_count": 407, "total_duration_ns": 13567474300, "load_duration_ns": 22196800, "prompt_eval_duration_ns": 38273000, "eval_duration_ns": 13334405000}`

Exact model response:

````text
<think> The user asks: "কৃত্ৰিম বুদ্ধিমত্তা কি? সহজ অসমীয়াত বুজাই দিয়ক।" They want a simple explanation of AI in Assamese. Must respond in Assamese, simple, short. No markdown. Provide concise explanation. </think> কৃত্ৰিম বুদ্ধিমত্তা (AI) মানে হৈছে যন্ত্ৰ বা কম্পিউটাৰক মানুহৰ দৰে ভাবি, শিকি, সিদ্ধান্ত ল'বলৈ সক্ষম কৰা। ই ডাটা বিশ্লেষণ, পেটাৰ্ন চিনাক্তকৰণ, ভাষা বুজা আদি কামত ব্যৱহাৰ হয়। সংক্ষেপে, AI মানে যন্ত্ৰক মানুহৰ দৰে চিন্তা আৰু কাম কৰিবলৈ শিকাই দিয়া।
````

#### top_p 0.75

- Request options: `{"temperature": 0.7, "num_predict": 1024, "top_p": 0.75}`
- Response time: 14.906 seconds
- Completion: `done=True`, `done_reason='stop'`
- Token/timing metadata: `{"prompt_eval_count": 233, "eval_count": 401, "total_duration_ns": 14900101200, "load_duration_ns": 40104200, "prompt_eval_duration_ns": 40939000, "eval_duration_ns": 14622577000}`

Exact model response:

````text
<think> User asks in Assamese: "What is artificial intelligence? Explain simply in Assamese." Need to respond in Assamese, simple, short, conversational. No markdown. Provide definition. </think> কৃত্ৰিম বুদ্ধিমত্তা (AI) মানে মেচিন বা কম্পিউটাৰ যি মানৱীয় বুদ্ধিমত্তা, যেনে বুজা, কাম কৰা, শিকাৰ আৰু সিদ্ধান্ত লোৱা দৰে কামসমূহ কৰিব পাৰে। ই ডাটা বিশ্লেষণ, নিয়ম অনুসৰণ আৰু সমস্যাবোৰ সমাধান কৰিবলৈ সঁচা কম্পিউটাৰ প্ৰগ্ৰাম ব্যৱহাৰ কৰে। সংক্ষেপে, AI মানে মেচিনক মানৱীয় ক্ষমতা দিয়া।
````

#### repeat_penalty 1.2

- Request options: `{"temperature": 0.7, "num_predict": 1024, "repeat_penalty": 1.2}`
- Response time: 13.57 seconds
- Completion: `done=True`, `done_reason='stop'`
- Token/timing metadata: `{"prompt_eval_count": 233, "eval_count": 401, "total_duration_ns": 13557967100, "load_duration_ns": 16830600, "prompt_eval_duration_ns": 40709000, "eval_duration_ns": 13258855000}`

Exact model response:

````text
<think> User asks: "What is artificial intelligence, explain simply in Assamese." Need answer short. Provide simple explanation of AI as computer doing tasks like learning languages etc., not thinking humanly but performing functions based on data and rules.

Write concise. </think> কৃত্ৰিম বুদ্ধি (AI) হ'লে, যন্ত্ৰ‑সাজা অথবা কণ্ঠ-চলিত প্ৰণালীটো নিজে একেলগে "শিখি" (learning) আরু সন্মুখভাৱে বিচাৰ-বিপাত, ৰীতি‑নিয়ম (rules), data‑analysis‍‌ ইত্যাদি কৌশলসহ “অভ্য়া” (action) বা “উত্তরে”) নিজ-নিজ ধৰণৰ চাপ‑সম্মুখি কই।  

এয়া ৱেব, smartphone, robot‍‌ আদি গ্ৰহিত নীতি-নিয়ম (rules)‑ভিত্তিক “AI”।  

**সাধাৰণতে**: AI = computer‍‌ + learning rules ⇒ works on its own. 
````

#### num_predict 1536

- Request options: `{"temperature": 0.7, "num_predict": 1536}`
- Response time: 11.927 seconds
- Completion: `done=True`, `done_reason='stop'`
- Token/timing metadata: `{"prompt_eval_count": 233, "eval_count": 357, "total_duration_ns": 11917296700, "load_duration_ns": 35130700, "prompt_eval_duration_ns": 37908000, "eval_duration_ns": 11657606000}`

Exact model response:

````text
<think> We need to answer in Assamese, simple, short. Explain AI in easy Assamese. No markdown. </think> কৃত্ৰিম বুদ্ধিমত্তা (AI) মানে হৈছে মেচিনবোৰে মানুহৰ দৰে যুক্তি প্ৰদান, ধাৰণা বুজি, সিদ্ধান্ত লোৱা ইত্যাদি কাম কৰাটো। মেচিনবোৰে ডাটা, নিয়ম আৰু সমস্যাবোৰ বিশ্লেষণ কৰি, নতুন তথ্যৰ ভিত্তিতে সিদ্ধান্ত বা কাৰ্য্য কৰে। সংক্ষেপে, ই মানুহৰ মগজুৰ দৰে ধৰণত কাম কৰা মেচিন।
````

### short_story

Prompt: আৰম্ভণি, মাজভাগ আৰু শেষ স্পষ্টকৈ থকা এখন চুটি অসমীয়া সাধুকথা লিখক।

| Configuration | Fluency | Grammar | Factual correctness | Repetition | Instruction following | Latency (s) | Completion | Notes |
|---|---:|---:|---:|---:|---:|---:|---|---|
| Production-like baseline | 1/5 | 1/5 | 1/5 | 5/5 | 1/5 | 33.587 | done=True, reason='length' | Gibberish/repeated phrase; hits the 1024-token limit. |
| Temperature 0.3 | 1/5 | 1/5 | 1/5 | 5/5 | 1/5 | 34.241 | done=True, reason='length' | Planning text loops on a proverb idea; hits the token limit without a story. |
| top_p 0.75 | 1/5 | 1/5 | 1/5 | 5/5 | 1/5 | 39.326 | done=True, reason='length' | Loops on what a proverb means and is truncated; no story. |
| repeat_penalty 1.2 | 1/5 | 1/5 | 1/5 | 2/5 | 1/5 | 17.986 | done=True, reason='stop' | Three-part labels appear, but the story text is mostly incoherent. |
| num_predict 1536 | 1/5 | 1/5 | 1/5 | 1/5 | 1/5 | 27.194 | done=True, reason='stop' | Ends normally but gives only the words beginning/middle/end, not a story. |

#### Production-like baseline

- Request options: `{"temperature": 0.7, "num_predict": 1024}`
- Response time: 33.587 seconds
- Completion: `done=True`, `done_reason='length'`
- Token/timing metadata: `{"prompt_eval_count": 256, "eval_count": 1024, "total_duration_ns": 33581744100, "load_duration_ns": 51719800, "prompt_eval_duration_ns": 580693000, "eval_duration_ns": 32880767999}`

Exact model response:

````text
<think> We need to produce a short Assamese moral story that's clear and understandable, with three parts: start, middle, end. Should be concise but include clarity. No formatting heavy, minimal formatting. Probably use simple sentences. Provide three sections separated by line breaks. Ensure Assamese script. </think> আৰম্ভণি  
এখন গাঁৱৰ নৌবাহী গৰুবাহী হেঁচা দিয়া হ'ল। গৰুবাহী হেঁচা দিয়া সময়ত তেখেত দৌৰতো বগা বাটত দৌৰি গাছপালাত বগা পাতা ধৰি গছত নেঙা নথাকিব।

মাজভাগ  
এক বেলা গাঁৱৰ বয়স্ক দেউলাৰ গছত গছত গা-ধৰা গৰুবাহী নৌবাহীক দেখিলে। গাঁৱৰ সকলোই বয়স্ক দেউলাক গালি দিছিল। কিন্তু গাঁৱৰ পুৰণি শিক্ষক গাঁৱৰ পাটত গছ গুচি থৈ যোৱা গৰুবাহীক সঁচা সঁচা গলাবাৰ গলাবাৰ সঁচা সঁচা সঁচা সঁচা সঁচা সঁচা সঁচা সঁচা সঁচা সঁচা সঁচা সঁচা সঁচা সঁচা সঁচা সঁচা সঁচা সঁচা সঁচা সঁচা সঁচা সঁচা সঁচা সঁচা সঁচা সঁচা সঁচা সঁচা সঁচা সঁচা সঁচা সঁচা সঁচা সঁচা সঁচা সঁচা সঁচা সঁচা সঁচা সঁচা সঁচা সঁচা সঁচা সঁচা সঁচা সঁচা সঁচা সঁচা সঁচা সঁচা সঁচা সঁচা সঁচা সঁচা সঁচা সঁচা সঁচা সঁচা সঁচা সঁচা সঁচা সঁচা সঁচা সঁচা সঁচা সঁচা সঁচা সঁচা সঁচা সঁচা সঁচা সঁচা
````

#### Temperature 0.3

- Request options: `{"temperature": 0.3, "num_predict": 1024}`
- Response time: 34.241 seconds
- Completion: `done=True`, `done_reason='length'`
- Token/timing metadata: `{"prompt_eval_count": 256, "eval_count": 1024, "total_duration_ns": 34234928200, "load_duration_ns": 24194800, "prompt_eval_duration_ns": 593532000, "eval_duration_ns": 33538455000}`

Exact model response:

````text
<think> User wants a short Assamese proverb (সাধুকথা) that is clear, with clear beginning, middle, end. Provide a short proverb. Should be in Assamese, minimal formatting. Provide maybe three lines? They said "আৰম্ভণি, মাজভাগ আৰু শেষ স্পষ্টকৈ থকা এখন চুটি অসমীয়া সাধুকথা লিখক।" Means write a short Assamese proverb that is clear, with clear beginning, middle, end. Could be a three-line proverb? Provide a short proverb like "অতি পলায়ন নকৰে, সঁচা হ'লে সঁচা হ'ব". Not sure. Maybe "অতি পলায়ন নকৰে, সঁচা হ'লে সঁচা হ'ব". That's not clear. Provide a simple proverb: "অতি পলায়ন নকৰে, সঁচা হ'লে সঁচা হ'ব". Not clear. Maybe "অতি পলায়ন নকৰে, সঁচা হ'লে সঁচা হ'ব". Hmm.

Better: "অতি পলায়ন নকৰে, সঁচা হ'লে সঁচা হ'ব". Not.

Maybe "অতি পলায়ন নকৰে, সঁচা হ'লে সঁচা হ'ব". Not.

Let's think of a proverb that is clear: "অতি পলায়ন নকৰে, সঁচা হ'লে সঁচা হ'ব". Not.

Maybe "অতি পলায়ন নকৰে, সঁচা হ'লে সঁচা হ'ব". Not.

Perhaps "অতি পলায়ন নকৰে, সঁচা হ'লে সঁচা হ'ব". Not.

Let's pick a well-known Assamese proverb: "অতি পলায়ন নকৰে, সঁচা হ'লে সঁচা হ'ব". Not.

Maybe "অতি পলায়ন নকৰে, সঁচা হ'লে সঁচা হ'ব". Not.

Could be "অতি পলায়ন নকৰে, সঁচা হ'লে সঁচা হ'ব". Not.

Let's think of a proverb about honesty: "অতি পলায়ন নকৰে, সঁচা হ'লে সঁচা হ'ব". Not.

Maybe "অতি পলায়ন নকৰে, সঁচা হ'লে সঁচা হ'ব". Not.

Maybe "অতি পলায়ন নকৰে, সঁচা হ'লে সঁচা হ'ব". Not.

Let's try "অতি পলায়ন নকৰে
````

#### top_p 0.75

- Request options: `{"temperature": 0.7, "num_predict": 1024, "top_p": 0.75}`
- Response time: 39.326 seconds
- Completion: `done=True`, `done_reason='length'`
- Token/timing metadata: `{"prompt_eval_count": 256, "eval_count": 1024, "total_duration_ns": 39310540800, "load_duration_ns": 25415300, "prompt_eval_duration_ns": 581646000, "eval_duration_ns": 38631310000}`

Exact model response:

````text
<think> User wants a short Assamese proverb that is clear at beginning, middle, end. Provide a proverb that is clear at each part. Probably "আৰম্ভণি, মাজভাগ, শেষ" meaning "beginning, middle, end". Maybe they want a proverb that can be read at any part and still make sense. Could be "যুক্তি হোৱা তেনে সঁচা মতামত" no. Need something like "সঁচা গুণে সঁচা মানে" hmm.

Maybe give a short proverb that reads the same at start, middle, end? Could be "বৈশাখী বধু" no.

Better: "অধিক নাছিলে কম নাছিলে, তেনেই বঁটা দিবা" no.

Idea: "যদি তুমি কোনো সঁচা কথা কোৱা, তেন্তে তুমি তোমাৰ সঁচা মানসিকতা পাবা।" Not clear.

Maybe give a proverb that can be read from any side: "সঁচা মানুহে সঁচা মন ধৰা কৰে" no.

Probably they want a proverb that is clear at beginning, middle, end, like "আৰম্ভণি: শুদ্ধ হ'ব, মাজভাগ: শান্তি, শেষ: সঁচা ফল". Could be "সঁচা বাটে সঁচা ফল পাবা". But that's not a proverb.

Better: "সঁচা কথা সঁচা মনে হৈ থাকে". No.

Maybe give a proverb that can be read from any side: "বাঁহী গছত গছত বাঁহী গছত গছত গছত গছত গছত গছত গছত গছত গছত গছত গছত গছত গছত গছত গছত গছত গছত গছত গছত গছত গছত গছত গছত গছত গছত গছত গছত গছত গছত গছত গছত গছত গছত গছত গছত গছত গছত গছত গছত গছত গছত গছত গছত গছত গছত গছত গছত গছত গছত গছত গছত গছত গছত গছত গছত গছত গছত গছত গছত গছত গছত গছত গছত গছত গছত গছত গছত গছত গছত গছত গছত গছত গ
````

#### repeat_penalty 1.2

- Request options: `{"temperature": 0.7, "num_predict": 1024, "repeat_penalty": 1.2}`
- Response time: 17.986 seconds
- Completion: `done=True`, `done_reason='stop'`
- Token/timing metadata: `{"prompt_eval_count": 256, "eval_count": 462, "total_duration_ns": 17980336800, "load_duration_ns": 100084000, "prompt_eval_duration_ns": 578922000, "eval_duration_ns": 17160924000}`

Exact model response:

````text
<think> The user asks in Assamese: "Write a short clear, concise Assamese Buddhist story with starting part, middle and ending clearly marked." They want three parts of the tale. Should be brief but include start, middle, end.

We need to produce minimal formatting; could use simple headings like আৰম্ভনি:, শেষ: . Provide a concise short Buddhist story in Assamese with clear sections for beginning, middle and ending.

Make sure answer is as short as possible. Use natural conversational tone but keep it succinct.

Let's produce something about an old monk who finds peace after leaving worldly life etc? Keep simple narrative.

Will use line breaks maybe okay; minimal formatting like separate paragraphs separated by blank lines or just newlines.

We'll write: আৰম্ভনি:, then story, ending with "শেষ". Provide three sections separately. Ensure Assamese script is correct.

Let's craft:

**আরম্ধান**: ...

But they said minimal formatting; could just label lines? Probably okay to use headings like সূচনা:, মধ্‌্य: , শেষ:. Provide short story. </think> **সুদিকি (আরম্ভান)**  
বৌদ্ধ-পঠি, এনে গা-ফূৰি‑শ্য়াল।  
খাই সুয়া, ৰিজি‍‌;  

**মদ্ধ্য (চরিত্র)**  
এক বহনে‑প্ৰাণী।

---

*... শেষ*: 

সুভা, অলি‍‌;  

**উদ্যোগ (মূখ)**
বিচ্ছিন্ন‑নাই।  
````

#### num_predict 1536

- Request options: `{"temperature": 0.7, "num_predict": 1536}`
- Response time: 27.194 seconds
- Completion: `done=True`, `done_reason='stop'`
- Token/timing metadata: `{"prompt_eval_count": 256, "eval_count": 755, "total_duration_ns": 27177594800, "load_duration_ns": 35957700, "prompt_eval_duration_ns": 32029000, "eval_duration_ns": 26921072000}`

Exact model response:

````text
<think> User asks: "আৰম্ভণি, মাজভাগ আৰু শেষ স্পষ্টকৈ থকা এখন চুটি অসমীয়া সাধুকথা লিখক।" So they want a short Assamese proverb that is clear for beginning, middle, and end (maybe three parts). Provide a concise proverb. Could be "আৰম্ভণি: সঁচা কথা ক'লে, মাজভাগ: সঁচা কথা ক'লে, শেষ: সঁচা কথা ক'লে" not that. Actually a proverb about three parts maybe "আৰম্ভণি মাজভাগ শেষ", could be "সুধু কাম কৰিব, শেষত শিকিব". Need to be short. Provide three lines: beginning, middle, end. So maybe "আৰম্ভণি কাম কৰা, মাজভাগ বিশ্বাস, শেষত শুদ্ধতা". Not proverb. Maybe "আৰম্ভণি গৰাকী হ'ল, মাজভাগ শূন্য, শেষ হ'ল শুদ্ধ". Hard.

Probably give a well-known Assamese proverb: "আৰম্ভণি কাম, মাজভাগ সময়, শেষ হ'ল ফল". Not clear.

Better give a proverb that can be interpreted as beginning, middle, end. For instance: "আৰম্ভণি সঁচা, মাজভাগ সঁচা, শেষত সঁচা". That's too simple.

Maybe they want a proverb that can be read as three parts: "আৰম্ভণি: সঁচা, মাজভাগ: সঁচা, শেষ: সঁচা". Not.

Perhaps they want a proverb that literally can be split into three sections: "আৰম্ভণি মাজভাগ শেষ". That is the whole phrase.

So I'll give a short proverb: "আৰম্ভণি মাজভাগ শেষ". That's three parts: beginning, middle, end.

Provide in Assamese. </think> আৰম্ভণি মাজভাগ শেষ।
````

### hardware_software

Prompt: হাৰ্ডৱেৰ আৰু ছফ্টৱেৰৰ মাজৰ পাৰ্থক্য অসমীয়াত বুজাই দিয়ক।

| Configuration | Fluency | Grammar | Factual correctness | Repetition | Instruction following | Latency (s) | Completion | Notes |
|---|---:|---:|---:|---:|---:|---:|---|---|
| Production-like baseline | 2/5 | 2/5 | 2/5 | 1/5 | 3/5 | 21.097 | done=True, reason='stop' | Core distinction is partly right; examples and some phrasing are confused. |
| Temperature 0.3 | 2/5 | 2/5 | 2/5 | 1/5 | 3/5 | 23.518 | done=True, reason='stop' | Definitions are partly recognizable; software/hardware relationship is misstated. |
| top_p 0.75 | 3/5 | 3/5 | 3/5 | 1/5 | 4/5 | 21.846 | done=True, reason='stop' | Most relevant comparison here, but claims hardware works independently of software. |
| repeat_penalty 1.2 | 1/5 | 1/5 | 2/5 | 1/5 | 1/5 | 6.963 | done=True, reason='stop' | Final answer is mostly English/mixed language, contrary to instruction. |
| num_predict 1536 | 2/5 | 2/5 | 2/5 | 1/5 | 3/5 | 19.386 | done=True, reason='stop' | Basic distinction is present, but examples and conclusion are inaccurate/unclear. |

#### Production-like baseline

- Request options: `{"temperature": 0.7, "num_predict": 1024}`
- Response time: 21.097 seconds
- Completion: `done=True`, `done_reason='stop'`
- Token/timing metadata: `{"prompt_eval_count": 245, "eval_count": 629, "total_duration_ns": 21088870600, "load_duration_ns": 63529400, "prompt_eval_duration_ns": 572565000, "eval_duration_ns": 20327454000}`

Exact model response:

````text
<think> User asks in Assamese: "Explain the difference between hardware and software in Assamese." Need to respond in Assamese, short, simple. Provide definitions. No markdown. </think> হাৰ্ডৱেৰ (Hardware) মানে মেচিনেৰে থকা বাস্তৱিক অংশ, যেনে কম্পিউটাৰৰ মডেল, মেম’ৰি, ড্ৰাইভাৰ, মাউণ্ট, পেন, কম্পিউটাৰ কেচ ইত্যাদি। ইয়াত কোনো সংখ্যা, চিপ বা কেশৰ সমান কোনো কাজ কৰে।

ছফ্টৱেৰ (Software) মানে কম্পিউটাৰত চলা প্ৰগ্ৰাম, মডিউল, এপ্‌লিকেশ্যন, এডিটৰ, সফটৱেৰ ডেভেলপমেণ্ট টুল আদিৰ কোড। ই ডাটা, তথ্য আৰু কম্পিউটাৰক কিদৰে চলিব লাগিব সেই নিয়মবোৰ ধাৰণ কৰে।

সংক্ষেপে, হাৰ্ডৱেৰ মেচিনেৰে সৃষ্ট বাস্তৱিক অংশ, যেতিয়া ছফ্টৱেৰ হৈছে কম্পিউটাৰক কাম কৰাত সহায়ক নিয়ম আৰু প্ৰগ্ৰাম।
````

#### Temperature 0.3

- Request options: `{"temperature": 0.3, "num_predict": 1024}`
- Response time: 23.518 seconds
- Completion: `done=True`, `done_reason='stop'`
- Token/timing metadata: `{"prompt_eval_count": 245, "eval_count": 727, "total_duration_ns": 23511823500, "load_duration_ns": 28982200, "prompt_eval_duration_ns": 33766000, "eval_duration_ns": 23213082000}`

Exact model response:

````text
<think> We need to explain difference between hardware and software in Assamese, simple conversational tone, short. No markdown. </think> হাৰ্ডৱেৰ (হাৰ্ডৱেৰ) মানে যি শারীৰিক যন্ত্ৰ‑সামগ্ৰী, যেনে কম্পিউটাৰৰ মাউণ্ট, মাইক্ৰ’ফোন, স্ক্ৰীণ, পেন, কেবল, মেমৰি ড্ৰাইভ, পাৱাৰ সাপ্লাই আদি। এইবোৰ সঁচা পদাৰ্থ, যি কম্পিউটাৰ বা অন্য যন্ত্ৰক চলাবলৈ আৰু তথ্য সংৰক্ষণ কৰিবলৈ ব্যৱহাৰ হয়।

ছফ্টৱেৰ (ছফ্টৱেৰ) মানে কম্পিউটাৰত চলা কোড, প্ৰগ্ৰাম, অথবা ব্যৱহাৰকাৰীৰ বাবে দেখা যোৱা প্ৰদৰ্শনী। ই হাৰ্ডৱেৰৰ সৈতে মিলি যোৱা নোহোৱা; ই কেৱল কম্পিউটাৰত সংৰক্ষিত ডাটা আৰু প্ৰক্ৰিয়া কৰিবলগীয়া নিয়ম বা কোড। উদাহৰণস্বৰূপে, মাইক্ৰ’ছফট ওয়াইন্ডোজ, গুগল চাৰ্চ, আৰু স্ক্ৰীণশ্বট এপ্লিকেশ্যন সকলো ছফ্টৱেৰ।
````

#### top_p 0.75

- Request options: `{"temperature": 0.7, "num_predict": 1024, "top_p": 0.75}`
- Response time: 21.846 seconds
- Completion: `done=True`, `done_reason='stop'`
- Token/timing metadata: `{"prompt_eval_count": 245, "eval_count": 604, "total_duration_ns": 21837898600, "load_duration_ns": 42443000, "prompt_eval_duration_ns": 42881000, "eval_duration_ns": 21375090000}`

Exact model response:

````text
<think> We need to explain hardware and software differences in Assamese, simple, short. No markdown. </think> হাৰ্ডৱেৰ মানে কম্পিউটাৰৰ ভিতৰত থকা শারীৰিক উপাদান—মাইক্রোপ্ৰসেছৰ, মেম'ৰি, ডিস্ক, কেব্‌ল, কেমেৰা আদি। এইবোৰ কাম কৰাত কোনো কম্পিউটাৰ এপ্‌লিকেশ্যন নথাকিলেও স্বতন্ত্ৰভাৱে কাম কৰে।

ছফ্টৱেৰ হৈছে সেই কম্পিউটাৰ এপ্‌লিকেশ্যন বা প্ৰগ্ৰাম যি হাৰ্ডৱেৰৰ সহায়ত কাম কৰে। ইয়াত অফিচ সফটৱেৰ, গেম, অ্যান্টিভাইৰাছ, ব্যাকআপ টুল আদি অন্তর্ভুক্ত। ছফ্টৱেৰ হাৰ্ডৱেৰৰ সৈতে মিলি কম্পিউটাৰক কাম কৰাত সক্ষম কৰে।

সংক্ষেপে: হাৰ্ডৱেৰ শারীৰিক উপাদান, ছফ্টৱেৰ তাৰে কাজ কৰা প্ৰগ্ৰাম।
````

#### repeat_penalty 1.2

- Request options: `{"temperature": 0.7, "num_predict": 1024, "repeat_penalty": 1.2}`
- Response time: 6.963 seconds
- Completion: `done=True`, `done_reason='stop'`
- Token/timing metadata: `{"prompt_eval_count": 245, "eval_count": 198, "total_duration_ns": 6958549100, "load_duration_ns": 30408300, "prompt_eval_duration_ns": 38344000, "eval_duration_ns": 6648486000}`

Exact model response:

````text
<think> User asks: "Explain the difference between hardware and software in Assamese." Need to respond concise, minimal formatting. Provide explanation of both definitions.

We must speak Assamese only. No markdown needed.

Let's craft short answer:

"Hardware হৈছে computer‑systemৰ physical components – CPU, RAM, storage, keyboard etc., while software is programs and applications that run on hardware to perform tasks."

Make it clear but concise. </think> Hardware = computer- systemৰ physical parts (CPU, RAM, disk, কিব’র্ড)।  
Software = সেই hardware‑এ চালনা হ'বলগিয়া programs and applications যিবোৰ user‑interface, data processing আদি কাম কৰে।
````

#### num_predict 1536

- Request options: `{"temperature": 0.7, "num_predict": 1536}`
- Response time: 19.386 seconds
- Completion: `done=True`, `done_reason='stop'`
- Token/timing metadata: `{"prompt_eval_count": 245, "eval_count": 536, "total_duration_ns": 19366348900, "load_duration_ns": 39907900, "prompt_eval_duration_ns": 576626000, "eval_duration_ns": 18604537000}`

Exact model response:

````text
<think> The user asks in Assamese: "হাৰ্ডৱেৰ আৰু ছফ্টৱেৰৰ মাজৰ পাৰ্থক্য অসমীয়াত বুজাই দিয়ক।" They want explanation of difference between hardware and software in Assamese. Need to respond short, simple, conversational, no markdown. Provide explanation. Use minimal words. Should be concise but cover key points. Probably mention hardware is physical, software is program, etc. Provide in Assamese. </think> হাৰ্ডৱেৰ মানে হ’ল যিবোৰ বস্তু‑সামগ্ৰী বা যন্ত্ৰ-যন্ত্ৰ (মেকা, টেবলেট, কেবল, মাউচ ইত্যাদি) যি কোনো কম্পিউটাৰ বা ডিভাইচত সজীৱ হৈ থাকে; ই সঁচাকৈ কোনো কাম কৰে। ছফ্টৱেৰ মানে হ’ল বিচ্ছিন্ন তথ্য‑সমূহ, কোড, অথবা নিৰ্দেশনা যি কম্পিউটাৰৰ হাৰ্ডৱেৰক চলাই থাকে। তেনেকৈ, হাৰ্ডৱেৰ হৈছে ক্ৰান্তি, ছফ্টৱেৰ হৈছে বাণী।
````

## Interpretation

No configuration was consistently better across all six prompts. Lower temperature produced the clearest CPU explanation in this small sample, but it did not repair the photosynthesis misunderstanding or repeated Assam sentences. Increasing `num_predict` let the story request stop normally, but the result still was not a story. A `repeat_penalty` of 1.2 did not prevent repeated text or English thinking text. The 27/30 visible `<think>` result shows that the `think: false` API field did not reliably suppress those tags for this model/runtime.

This experiment uses one generation per prompt and configuration. Stochastic variation, subject knowledge, and prompt sensitivity are not controlled by one sample. Do not treat these observations as a quality benchmark or change production settings based only on this run. Compare the exact responses above; no application or model configuration was modified.
