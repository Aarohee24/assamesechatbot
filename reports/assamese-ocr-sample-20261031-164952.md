# Assamese OCR Sample Evaluation

- Generated: 2026-10-31T16:50:24+05:30
- Tesseract: `tesseract v5.5.3.20260724`
- Installed languages: `asm`
- Renderer: pypdfium2
- Rendering: 300 DPI
- OCR: Tesseract LSTM (`--oem 1`, language `asm`), page segmentation modes 3, 6, 11
- Scope: six selected sample pages only; no full-book OCR or extracted-text replacement.
- Original PDFs and existing raw extraction files were not modified.

## Results

| PDF page | Sample reason | Native Assamese-block letters | OCR PSM 3 | OCR PSM 6 | OCR PSM 11 |
|---|---|---:|---:|---:|---:|
| `Ami Aru Amar Paribesh_Class V_Assamese.pdf` p.3 | font-mapping and image-rich cover | 0 | 22 | 78 | 121 |
| `Ankuran (Saptam Bhag) (Language (L1))_Class 7_Assamese medium.pdf` p.3 | font-mapping and image-rich cover | 0 | 65 | 84 | 124 |
| `Samaj Bichitra_Class VI_Textbook_Assamese.pdf` p.3 | font-mapping and image-rich cover | 0 | 40 | 64 | 247 |
| `Science_Class VI_Part 1_Assamese.pdf` p.4 | suspicious text mapping and embedded image | 0 | 98 | 103 | 91 |
| `Unmesh I-Class VI-Assamese.pdf` p.4 | suspicious text mapping and embedded images | 0 | 179 | 197 | 197 |
| `Assamese.pdf` p.7 | scanned text page with no extracted text | 0 | 1574 | 1575 | 1665 |

## Per-page comparison

### Ami Aru Amar Paribesh_Class V_Assamese.pdf — page 3

- Sample rationale: font-mapping and image-rich cover
- Original rendered page: `Ami Aru Amar Paribesh_Class V_Assamese-page-3.png` (2481 × 3331, SHA-256 `558d829648ce92062a7509897e4aadf25892afce964c05b522c3bcc9985445da`)
- Native extraction metrics: `{"characters": 164, "alphabetic_characters": 53, "assamese_block_letters": 0, "assamese_block_letter_ratio": 0.0, "whitespace_words": 65, "replacement_characters": 0}`
- Visual comparison status: OCR text requires manual reading against the saved page image. Character/script metrics alone are not an accuracy measure.

#### Existing raw extracted text (unchanged)

```text
    ¡ e  ¸   ~ å ¶  é i ¹   È t   ¢   Q È  °   ~ å ¶ t  ¶ y    È Í ¡   ¢  «
°  G v ¶  ¸  t
Copyright-SCERT, Assam 
 not to be republished
```
#### Tesseract PSM 3

- Settings: language `asm`, OEM 1, PSM 3, 300 DPI
- Metrics: `{"characters": 47, "alphabetic_characters": 22, "assamese_block_letters": 22, "assamese_block_letter_ratio": 1.0, "whitespace_words": 8, "replacement_characters": 0}`

```text
(পাঠ্য তথা অভ্যসন পুথি)

পঞ্চম শ্রেণীৰ বাবে  &-
```

#### Tesseract PSM 6

- Settings: language `asm`, OEM 1, PSM 6, 300 DPI
- Metrics: `{"characters": 286, "alphabetic_characters": 78, "assamese_block_letters": 78, "assamese_block_letter_ratio": 1.0, "whitespace_words": 40, "replacement_characters": 0}`

```text
৷৷৷, উচ                খএ7৷1| 7
তৃতীয় ভাগ
(পাঠ্য তথা অভ্যসন পুথি)            ৰব
ঢ়             পঞ্চম শ্রেণীৰ বাবে    ৰ
ঢ়     ৬.           ?               ৰ
"]7/            !     ৰ্দ            -   ৰ *
+ ১   ৰ    ৰ     ঁ
ইঞ' =
প্ৰস্তুতকৰণ
ৰাজ্যিক শিক্ষা-ণৰেষণা আৰু প্ৰশিক্ষণ পৰিষদ, অসম
```

#### Tesseract PSM 11

- Settings: language `asm`, OEM 1, PSM 11, 300 DPI
- Metrics: `{"characters": 295, "alphabetic_characters": 121, "assamese_block_letters": 121, "assamese_block_letter_ratio": 1.0, "whitespace_words": 48, "replacement_characters": 0}`

```text
[= [ছ]

ৰু

দূ

ৰ

১7417

788 আমি আৰু আমাৰ পৰিৱেশ

তৃতীয় ভাগ

(পাঠ্য তথা অভ্যসন পুথি)

|

ৰণ

পঞ্চম শ্ৰেণীৰ বাবে  মতা

(১৫

'/{

৬১৮.২

৩০ চি)

এ্্জ্ত

চ

"|

প্ৰস্তুতকৰণ

ৰাজ্যিক শিক্ষা-গৱেষণা আৰু প্ৰশিক্ষণ পৰিষদ, অসম

ভ্রঁ্তন্ত্মরা ব্ু

নাম -

বিদ্যালয়ৰনাম

বিদ্যালয় শিক্ষা বিভাগ, অসম চৰকাৰ
```

### Ankuran (Saptam Bhag) (Language (L1))_Class 7_Assamese medium.pdf — page 3

- Sample rationale: font-mapping and image-rich cover
- Original rendered page: `Ankuran (Saptam Bhag) (Language (L1))_Class 7_Assamese medium-page-3.png` (2422 × 3249, SHA-256 `05295b5b3012099c0b2a1c2a05b6472d132761b72f94605af6d7d177aacaaf1f`)
- Native extraction metrics: `{"characters": 557, "alphabetic_characters": 94, "assamese_block_letters": 0, "assamese_block_letter_ratio": 0.0, "whitespace_words": 33, "replacement_characters": 0}`
- Visual comparison status: OCR text requires manual reading against the saved page image. Character/script metrics alone are not an accuracy measure.

#### Existing raw extracted text (unchanged)

```text
’—ﬂ≈¡1Ì
ø˙é¬± [õ∂±Ôø˜ﬂ¡] ø¬ıˆ¬±·
’¸˜ ‰¬1ﬂ¡±1
Ú±˜ –...................................................................................................................
Œ|Ìœ.....................................˙±‡±.........................Œ1±˘ Ú•§1............................
ø¬ı√…±˘˚˛............................................................................‰¬Ú................................
¸5˜ ˆ¬±·
[¬Û±Í¬… Ó¬Ô± ’ˆ¬…¸Ú ¬Û≈øÔ]
¸5˜ Œ|Ìœ1 ¬ı±À¬ı
õ∂dÓ¬ﬂ¡Ó«¬±
1±øÊ√…ﬂ¡ ø˙é¬±-·Àª¯∏Ì± ’±1n∏ õ∂ø˙é¬Ì ¬Ûø1¯∏√, ’¸˜
Copyright-SCERT, Assam 
not to be republished
```
#### Tesseract PSM 3

- Settings: language `asm`, OEM 1, PSM 3, 300 DPI
- Metrics: `{"characters": 119, "alphabetic_characters": 65, "assamese_block_letters": 65, "assamese_block_letter_ratio": 1.0, "whitespace_words": 15, "replacement_characters": 0}`

```text
সপ্তম শ্রেণীৰ বাবে পাত

প্ৰস্তুতকৰ্তা
ৰাজ্যিক শিক্ষা-গপৱেষণা আৰু প্ৰশিক্ষণ পৰিষদ,অসম

শিক্ষা (প্ৰাথমিক) বিভাগ
অসম চৰকাৰ
```

#### Tesseract PSM 6

- Settings: language `asm`, OEM 1, PSM 6, 300 DPI
- Metrics: `{"characters": 259, "alphabetic_characters": 84, "assamese_block_letters": 84, "assamese_block_letter_ratio": 1.0, "whitespace_words": 34, "replacement_characters": 0}`

```text
৷, ৷ অংকুৰণ
তব ৰ             সপ্তম ভাগ     ত
্‌            সপ্তম শ্ৰেণীৰ বাবে  ৰ
্‌               প্ৰস্তুতকৰ্তা     ৮171" |
ৰাজ্যিক শিক্ষা-গৰেষণা আৰু প্ৰশিক্ষণ পৰিষদ,অসম       _
চু                        র্দ্্_
দদা ্ত্ঙে ৮; ২
শিক্ষা (প্ৰাথমিক) বিভাগ
অসম চৰকাৰ
```

#### Tesseract PSM 11

- Settings: language `asm`, OEM 1, PSM 11, 300 DPI
- Metrics: `{"characters": 635, "alphabetic_characters": 124, "assamese_block_letters": 124, "assamese_block_letter_ratio": 1.0, "whitespace_words": 51, "replacement_characters": 0}`

```text
অংকুৰণ

সপ্তম ভাগ

(পাঠ্য তথা অভ্যসন পুথি)  পম

[মাও[দ]

পো

ৰ

সপ্তম শ্রেণীৰ বাবে

চু" 3

প্ৰস্তুতকৰ্তা

চ]1

171

ৰাজ্যিক শিক্ষা-গ|ৱেষণা আৰু প্ৰশিক্ষণ পৰিষদ,অসম

সৰ

গোল

৷

ভ্ছছ

2

॥  ৰ

ঢ়

ত) বৰ

৷ চেঃ

৬৩০৬৩৩০৩০৩৩০৩৩৩৩৩৩৩৩৩৩০৩৩৩০৩৩৩০৩৩৩৩৩৩০৩০৩৩৩৩৩৩৩৩৩০৩৩৩৩৩৩৩৩৩৩৩৩৩৩৩৩৩৩৩৩৩৩০৩৩৩৩৩৩৩৩৩৩০৩৩০৩৩৩৩৩৩৩৩৩৩০৩৩৩৩৩৩৩৩৩৩০৩৩৩৩৩৩৩৩৩৩৩০৩০৩৩৩৩৩৩৩০৩৩০৩

(জ্রেণী:..১১১১১১১.১০০০০০৷                          শাখা

৬৬০৩৬০৬০০০০৬৩০৩০৩০৩০৩০৩০৩০৩০০৩০৩০০০০০০০০০৩

ৰোল নম্বৰ

৬৬০৬০৬০০০০৬৩০৩০৩০৩০৩০৩০৩০০৩০৩০৩০৩০৩০৩০০০০০০০০০৩

বিদ্যালয়...................১১১০০০০০০০০০০০০০০০০০০০০       চল, ,,,১১১,,,,,,,,,,,,,,,,,,,,,,০,

শিক্ষা (প্ৰাথমিক) বিভাগ

অসম চৰকাৰ
```

### Samaj Bichitra_Class VI_Textbook_Assamese.pdf — page 3

- Sample rationale: font-mapping and image-rich cover
- Original rendered page: `Samaj Bichitra_Class VI_Textbook_Assamese-page-3.png` (2481 × 3508, SHA-256 `ca5967419bc9da01417485a80210d3791858fcf13fb64c8ea8f7b399709f4cc5`)
- Native extraction metrics: `{"characters": 236, "alphabetic_characters": 142, "assamese_block_letters": 0, "assamese_block_letter_ratio": 0.0, "whitespace_words": 30, "replacement_characters": 0}`
- Visual comparison status: OCR text requires manual reading against the saved page image. Character/script metrics alone are not an accuracy measure.

#### Existing raw extracted text (unchanged)

```text
ø¸‡Â Î|íÏ1 Âõ±ËÂõ Âü÷±æÃ ¿Âõ:±ò1 Âó±êÂÉÂóÅ¿ï
¿ÂõðÃÉ±ùûþ ¿úŽÂ± ¿ÂõöÂ±á, Õü÷ äÂ1ßÁ±1
ü÷±æÃ ¿Âõ¿äÂS± 
¦¤ËðÃú-¿ÂõËðÃú1 ü÷±æÃ Âó¿1äÂûþ
›¶íûþò Ð 1±¿æÃÉßÁ ¿úŽÂ±-áË»ø¸í± Õ±1n¸ ›¶¿úŽÂí Âó¿1ø¸ðÃ, Õü÷
Copyright-SCERT, Assam 
 not to be republished
```
#### Tesseract PSM 3

- Settings: language `asm`, OEM 1, PSM 3, 300 DPI
- Metrics: `{"characters": 76, "alphabetic_characters": 40, "assamese_block_letters": 40, "assamese_block_letter_ratio": 1.0, "whitespace_words": 11, "replacement_characters": 0}`

```text
ষষ্ঠ শ্ৰেণীৰ বাবে সমাজ বিজ্ঞানৰ পাঠ্যপুথি

বিদ্যালয় শিক্ষা বিভাগ, অসম চৰকাৰ
```

#### Tesseract PSM 6

- Settings: language `asm`, OEM 1, PSM 6, 300 DPI
- Metrics: `{"characters": 152, "alphabetic_characters": 64, "assamese_block_letters": 64, "assamese_block_letter_ratio": 1.0, "whitespace_words": 24, "replacement_characters": 0}`

```text
|ু্+"]])
ষষ্ঠ শ্ৰেণীৰ বাবে সমাজ বিজ্ঞানৰ পাঠ্যপুথি
ই                 পৰ্ব
1;    ধন নাতি শিল গবা আৰু তপিল'ন পৰিব, অসম *
বিদ্যালয় শিক্ষা বিভাগ, অসম চৰকাৰ
```

#### Tesseract PSM 11

- Settings: language `asm`, OEM 1, PSM 11, 300 DPI
- Metrics: `{"characters": 564, "alphabetic_characters": 247, "assamese_block_letters": 247, "assamese_block_letter_ratio": 1.0, "whitespace_words": 115, "replacement_characters": 0}`

```text
[দ] 3 [দ]

1.

বচ:

ৰ] 7

"113

ষষ্ঠ শ্ৰেণীৰ বাবে সমাজ বিজ্ঞানৰ পাঠ্যপুথি

“প্যাৰ

ধ!

[উ

ৰু

ৰঃ

/*

=

0 ভু

=

চী

=

প্ৰণয়ন ঃ ৰাজ্যিক শিক্ষা-শগৱেষণা আৰু প্ৰশিক্ষণ পৰিষদ, অসম

ৰ

হেছে জ়়নল জজ  ঢ যগখধ লয় জজ ৷৷ য় (ঙজ 6টজিজঁজ কয় জজ "(686 ((উ়[কক়ক=্ঞ

ভজ ভক্াভভক্ভা ভাভা ভাভা ভাভা তত ভাভাভীকী ভকতক ভক কভ ভকতক ভক ভীত কক কত ভকতত ভক তভক ত ভককভভী ককাক ভভী তত কভকতভভ ভকত ভক ককককতভকককত

বৱিদ্যথকৰ লাগিব এ%৬৬০২৮১%৬১৷৭১১১চ৭ত১০3৭০ ৭৭৬০২,

হহ য় "০" এ&ৌে&দছৰ হল ছোট এ এএঅ{ 6 লন ]ক ৷ ৷ এ যআ {= যো 1ৈেযউ়7া় ঁ ়' [হো ৷ এ এ ই ৰ ' এ

মাপ

বিদ্যালয় শিক্ষা বিভাগ, অসম চৰকাৰ
```

### Science_Class VI_Part 1_Assamese.pdf — page 4

- Sample rationale: suspicious text mapping and embedded image
- Original rendered page: `Science_Class VI_Part 1_Assamese-page-4.png` (2481 × 3508, SHA-256 `3b4b24a0b321325c9e7b145311714520d195004037debc2d1e5e21c6b8b8bc26`)
- Native extraction metrics: `{"characters": 804, "alphabetic_characters": 583, "assamese_block_letters": 0, "assamese_block_letter_ratio": 0.0, "whitespace_words": 117, "replacement_characters": 0}`
- Visual comparison status: OCR text requires manual reading against the saved page image. Character/script metrics alone are not an accuracy measure.

#### Existing raw extracted text (unchanged)

```text
Õ±÷±1 ¿Âõ:±ò/Amar Bijnan (Part -I) -A Bilingual Science textbook with Assamese language 
and English language for Class-VI,developed by SCERT, Assam, published by the Assam 
State Textbook Production & Corporation Limited, Guwahati on behalf of Govt. of Assam.
 FREE TEXTBOOK
ALL RIGHTS RESERVED : No reproduction in any form of this book, in whole or in 
part (except for brief quotation in critical articles or reviews) may be made without written 
authorization from the copyright authorities.
Copyright : State Council of Educational Research and Training (SCERT), Assam. 
›¶ï÷ öÂ±á : 2025
 
›¶ßÁ±úßÁ : Õü÷ äÂ1ßÁ±11 ÁZ±1± ¿Âõò±÷ÓùÏûþ±ÍßÁ ¿ÂõîÂ1í1 Âõ±ËÂõ Õü÷ 1±¿æÃÉßÁ Âó±êÂÉÂóÅ¿ï ›¶íûþò Õ±1n¸ 
›¶ßÁ±úò ¿òá÷ ¿ù¿÷ËéÂëÂ1 ÁZ±1± ›¶ßÁ±¿úîÂ Âó±êÂÉÂóÅ¿ï¼
÷Å^ßÁ  :
Copyright-SCERT, Assam 
not to be republished
```
#### Tesseract PSM 3

- Settings: language `asm`, OEM 1, PSM 3, 300 DPI
- Metrics: `{"characters": 895, "alphabetic_characters": 98, "assamese_block_letters": 98, "assamese_block_letter_ratio": 1.0, "whitespace_words": 111, "replacement_characters": 0}`

```text
আমাৰ বিজ্ঞান//৷৷ 81" }1]]}91৷ (3 1"( -]) -/% ]31]1]6081 9012006 16%00001 {1 /১৪৪৪110296 181160886
8100 ]71]9]19]1 18116088662 101" (4899-€],06%610]2760 ৮6% ০েম:ং], /১৪৪৪1]], 17>0[0]191]160 [0% 16 /১৯৪৪8]]]
১0৪০ [50000] 1"1000001011 &, €01])018.101] ][.1]]1[60, 008]181 011 02178] 01 070৮. 01 /১৪98]]].

]']$]]}, ']1],১%1]]১0)01<

এিএ].], ]ংাো|১5 ]ং1,১].]২৮]}}]) : ]খ০ 16[0100000801] 11] 01} 10]]] 01 019 0600], 11) "11016 01 1]
12800 (6৯%০০]){ 101 01161 00008.0011 11) গে10108| 81010169 01[' 16416%9) 1]]18% [0026 11802 ছ৮1||100{ ছঘা||[2]]
800701178001] 101] 16 ০০])ঘাা18]]{ 80010110629.

(:0])118]1{       র          508৮6 0:0011011 01 1+000800118] ]২০৪০৪1"0০]] 81710 '[181101116 (০৫:)7]২']"'), /২৪৪৪8]]].

প্ৰথম ভাগ              :              2025

প্রকাশক     ন    অসম চৰকাৰৰ দ্বাৰ৷ বিনামূলীয়াকৈ বিতৰণৰ বাবে অসম ৰাজ্যিক পাঠ্যপুথি প্রণয়ন আৰু
প্রকাশন নিগম লিমিটেডৰ দ্বাৰা প্রকাশিত পাঠ্যপুথি।
```

#### Tesseract PSM 6

- Settings: language `asm`, OEM 1, PSM 6, 300 DPI
- Metrics: `{"characters": 918, "alphabetic_characters": 103, "assamese_block_letters": 103, "assamese_block_letter_ratio": 1.0, "whitespace_words": 112, "replacement_characters": 0}`

```text
আমাৰ বিজ্ঞান//৷৷ 81" }1]]}91৷ (3 1"( -]) -/% ]31]1]6081 9012006 16%00001 {1 /১৪৪৪110296 181160886

8100 ]71]9]19]1 18116088662 101" (4899-€],06%610]2760 ৮6% ০েম:ং], /১৪৪৪1]], 17>0[0]191]160 [0% 16 /১৯৪৪8]]]

১0৪০ [50000] 1"1000001011 &, €01])018.101] ][.1]]1[60, 008]181 011 02178] 01 070৮. 01 /১৪98]]].
]]ংা(/,'][]/%]['[$0)01<

এিএ].], ]ংাো|১5 ]ং1,১].]২৮]}}]) : ]খ০ 16[0100000801] 11] 01} 10]]] 01 019 0600], 11) "11016 01 1]

12800 (6৯%০০]){ 101 01161 00008.0011 11) গে10108| 81010169 01[' 16416%9) 1]]18% [0026 11802 ছ৮1||100{ ছঘা||[2]]

800701178001] 101] 16 ০০])ঘাা18]]{ 80010110629.

(:0])118]1{       র          508৮6 0:0011011 01 1+000800118] ]২০৪০৪1"0০]] 81710 '[181101116 (০৫:)7]২']"'), /২৪৪৪8]]].

প্ৰথম ভাগ              :              2025

প্রকাশক     ন    অসম চৰকাৰৰ দ্বাৰ৷ বিনামূলীয়াকৈ বিতৰণৰ বাবে অসম ৰাজ্যিক পাঠ্যপুথি প্রণয়ন আৰু

প্রকাশন নিগম লিমিটেডৰ দ্বাৰা প্রকাশিত পাঠ্যপুথি।
মুদ্ৰক             ৰ
```

#### Tesseract PSM 11

- Settings: language `asm`, OEM 1, PSM 11, 300 DPI
- Metrics: `{"characters": 841, "alphabetic_characters": 91, "assamese_block_letters": 91, "assamese_block_letter_ratio": 1.0, "whitespace_words": 107, "replacement_characters": 0}`

```text
আমাৰ বিজ্ঞান//৷৷ 81" }1]]}91৷ (3 1"( -]) -/% ]31]1]6081 9012006 16%00001 {1 /১৪৪৪110296 181160886

8100 ]71]9]19]1 18116088662 101" (4899-€],06%610]2760 ৮6% ০েম:ং], /১৪৪৪1]], 17>0[0]191]160 [0% 16 /১৯৪৪8]]]

১0৪০ [50000] 1"1000001011 &, €01])018.101] ][.1]]1[60, 008]181 011 02178] 01 070৮. 01 /১৪98]]].

]']$]]}, ']1],১%1]]১0)01<

এিএ].], ]ংাো|১5 ]ং1,১].]২৮]}}]) : ]খ০ 16[0100000801] 11] 01} 10]]] 01 019 0600], 11) "11016 01 1]

12800 (6৯%০০]){ 101 01161 00008.0011 11) গে10108| 81010169 01[' 16416%9) 1]]18% [0026 11802 ছ৮1||100{ ছঘা||[2]]

800701178001] 101] 16 ০০])ঘাা18]]{ 80010110629.

0][))1189]1{

508৮6 0:0011011 01 1+000800118] ]২০৪০৪1"0০]] 81710 '[181101116 (০৫:)7]২']"'), /২৪৪৪8]]].

প্ৰথম ভাগ

2025

অসম চৰকাৰৰ দ্বাৰ৷ বিনামূলীয়াকৈ বিতৰণৰ বাবে অসম ৰাজ্যিক পাঠ্যপুথি প্রণয়ন আৰু

প্রকাশন নিগম লিমিটেডৰ দ্বাৰা প্রকাশিত পাঠ্যপুথি।
```

### Unmesh I-Class VI-Assamese.pdf — page 4

- Sample rationale: suspicious text mapping and embedded images
- Original rendered page: `Unmesh I-Class VI-Assamese-page-4.png` (2436 × 3224, SHA-256 `f854c45a33be8450eb5010403f5898b5e7819a527df74f6d75b664f584176e53`)
- Native extraction metrics: `{"characters": 442, "alphabetic_characters": 200, "assamese_block_letters": 0, "assamese_block_letter_ratio": 0.0, "whitespace_words": 189, "replacement_characters": 0}`
- Visual comparison status: OCR text requires manual reading against the saved page image. Character/script metrics alone are not an accuracy measure.

#### Existing raw extracted text (unchanged)

```text
¿ ò á ÷  ¿ ù ¿ ÷ Ë é Â ë Â 1  Á Z ± 1 ±  › ¶ ß Á ± ¿ ú î Â  Â ó ± ê Â É Â ó Å ¿ ï ¼
w o r k s h o p s ,  a p p r o v e d  b y  t h e  G o v e r n m e n t  o f  A s s a m  a n d  p u b l i s h e d  b y  t h e  A s s a m  
S t a t e  T e x t b o o k .  P r o d u c t i o n  a n d  P u b l i c a t i o n  C o r p o r a t i o n  L t d .  o n  b e h a l f  o f  
G o v e r n m e n t  o f  A s s a m .
Copyright-SCERT, Assam 
 not to be republished
```
#### Tesseract PSM 3

- Settings: language `asm`, OEM 1, PSM 3, 300 DPI
- Metrics: `{"characters": 962, "alphabetic_characters": 179, "assamese_block_letters": 179, "assamese_block_letter_ratio": 1.0, "whitespace_words": 116, "replacement_characters": 0}`

```text
[)][খ[[,৬]]; ])]২/%]][]/4[*] ]3]]/%("*: /%1] 111(2818020 |26স00-001]]-01]00001< 101"
(:1899-€[, 111 /*৪৪৪811]16962, 026%610]260 8110 16%416%%60 06%) ১৫.]"[২], /*৪৪৪]1]1] 11008]]
স্ণ01]18110])8, 8])[10%4620 0%া 076 00ঘ211]1]]611{ 01 /১৪৪8৪1]] 8110 |)700119|160 0 16 /৯৪৪৪[0]]
০০৪৮০ [68000], 1"0000001]] ৪8110 1]700|108001]}] (:0120180001[] ]/[0. 011 0811811 01
00ঘণ21111]621]1{ 01 /১৪৪৪]]].

['[1'"66 ][6%{[2001

/%]] [২192]19 1[(€6৪০1"৮60] : [0 16][00000101] 11] 811} [011]] 01 {]]19 00013:11] ঘ%৮11016 01
11] |)81"01]]8' [26 1118.092 1|]1000{ ছয|"1(21] 8010101178101] 1|"01]] ১৫)[২], /১৪৪৪]]],.

গৰন্থস্বত্ব       £$ ৰাজ্যিক শিক্ষা-গাৱেষণা আৰু প্ৰশিক্ষণ পৰিষদ,অসম
প্ৰথম প্ৰকাশ       ৰ    ২০২৪
$ _ £ঠ70 091/[ কাগজত মুদ্ৰিত পাঠ্যপুথি
প্রকাশক     ঃ অসম চৰকাৰৰ দ্বাৰা বিনামূলীয়াকৈ বিতৰণৰ বাবে অসম ৰাজ্যিক পাঠ্যপুথি প্ৰণয়ন
আৰু প্রকাশন নিগম লিমিটেডৰ দ্বাৰা প্রকাশিত পাঠ্যপুথি।
মুদ্ৰক       ঃ$ লাৱণ্য প্ৰিণ্টিং প্ৰেছ
চন্দ্ৰকান্ত হাজৰিকা পথ

তৰুণ নগৰ, গুৱাহাটী-৭৮১০০৫
```

#### Tesseract PSM 6

- Settings: language `asm`, OEM 1, PSM 6, 300 DPI
- Metrics: `{"characters": 1055, "alphabetic_characters": 197, "assamese_block_letters": 197, "assamese_block_letter_ratio": 1.0, "whitespace_words": 131, "replacement_characters": 0}`

```text
ন      [আছো আছা ডোমে তাই চোভা ো ছাৱা মো ছাইড ডোল আভা      [ত
[োখা্া},১5]]; ])];/%]]]/%[$] ]}]]/৯(*: /%1]] 111(2818060 (2800-001]1]-% 0110000]; 101
(:1899-€[, 111 /*৪৪৪811]16962, 026%610]260 8110 16%416%%60 06%) ১৫.]"[২], /*৪৪৪]1]1] 11008]]
স্ণ01]18110])8, 8])[10%4620 0%া 076 00ঘ211]1]]611{ 01 /১৪৪8৪1]] 8110 |)700119|160 0 16 /৯৪৪৪[0]]
০০৪৮০ [68000], 1"0000001]] ৪8110 1]700|108001]}] (:0120180001[] ]/[0. 011 0811811 01
(00%6211010]621][ 01 /১৪৪8]]].

]11"66 '[6%12001%
/&]] [২12]1(9 ][(২6৪০1"৮6€0] : [০0 16[1"00000101] 11] 811} [01]]] 01 019 [00131] ৮1012 01"
111 |)8[{ 1118) [06 18062 10|1000[ ছছ11[[21] 80(|101178{101] [1|"01]] ০৫]:]২][, /১৪৪৪]]].,
গ্ৰন্থস্বত্ব                    $ ৰাজ্যিক শিক্ষা-গাৱেষণা আৰু প্রশিক্ষণ পৰিষদ,অসম
প্ৰথম প্ৰকাশ                ৰ          ২০২৪
$ _ £ঠ70 091/[ কাগজত মুদ্ৰিত পাঠ্যপুথি

প্রকাশক       ঃ অসম চৰকাৰৰ দ্বাৰা বিনামূলীয়াকৈ বিতৰণৰ বাবে অসম ৰাজ্যিক পাঠ্যপুথি প্ৰণয়ন

আৰু প্রকাশন নিগম লিমিটেডৰ দ্বাৰা প্রকাশিত পাঠ্যপুথি।
মুদ্ৰক          ঃ$ লাৱণ্য প্ৰিণ্টিং প্ৰেছ

চন্দ্ৰকান্ত হাজৰিকা পথ

তৰুণ নগৰ, গুৱাহাটী-৭৮১০০৫
```

#### Tesseract PSM 11

- Settings: language `asm`, OEM 1, PSM 11, 300 DPI
- Metrics: `{"characters": 965, "alphabetic_characters": 197, "assamese_block_letters": 197, "assamese_block_letter_ratio": 1.0, "whitespace_words": 110, "replacement_characters": 0}`

```text
[োখা্া},১5]]; ])];/%]]]/%[$] ]}]]/৯(*: /%1]] 111(2818060 (2800-001]1]-% 0110000]; 101

(:1899-€[, 111 /*৪৪৪811]16962, 026%610]260 8110 16%416%%60 06%) ১৫.]"[২], /*৪৪৪]1]1] 11008]]

স্ণ01]18110])8, 8])[10%4620 0%া 076 00ঘ211]1]]611{ 01 /১৪৪8৪1]] 8110 |)700119|160 0 16 /৯৪৪৪[0]]

০০৪৮০ [68000], 1"0000001]] ৪8110 1]700|108001]}] (:0120180001[] ]/[0. 011 0811811 01

(য0%2110111211{ 01 /*৪৪৪1]].

[{1"66 [62001

/%]] [২192]19 1[(€6৪০1"৮60] : [0 16][00000101] 11] 811} [011]] 01 {]]19 00013:11] ঘ%৮11016 01

11] |)81"01]]8' [26 1118.092 1|]1000{ ছয|"1(21] 8010101178101] 1|"01]] ১৫)[২], /১৪৪৪]]],.

গ্ৰন্থস্বত্ব

ৰাজ্যিক শিক্ষা-গৱেষণা আৰু প্ৰশিক্ষণ পৰিষদ;অসম

প্ৰথম প্ৰকাশ

২০২৪

70 091/[. কাগজত মুদ্ৰিত পাঠ্যপুথি

অসম চৰকাৰৰ দ্বাৰা বিনামূলীয়াকৈ বিতৰণৰ বাবে অসম ৰাজ্যিক পাঠ্যপুথি প্ৰণয়ন

আৰু প্ৰকাশন নিগম লিমিটেডৰ দ্বাৰা প্রকাশিত পাঠ্যপুথি।

লাৱণ্য প্ৰিণ্টিং প্ৰেছ

চন্দ্ৰকান্ত হাজৰিকা পথ

তৰুণ নগৰ, গুৱাহাটী-৭৮১০০৫

[আঘৰৰৰৰৰেজেঘৰৰৰেে৪ী৪েোাৰাোোৰ]]মমভভভভভাভভেভতঙৰৰৰৰৰ
```

### Assamese.pdf — page 7

- Sample rationale: scanned text page with no extracted text
- Original rendered page: `Assamese-page-7.png` (2481 × 3507, SHA-256 `d55ebe0064feddd12a2484972c850ae13f6fa196aa3c2efe8d6d8538a0ccc1cb`)
- Native extraction metrics: `{"characters": 0, "alphabetic_characters": 0, "assamese_block_letters": 0, "assamese_block_letter_ratio": 0.0, "whitespace_words": 0, "replacement_characters": 0}`
- Visual comparison status: OCR text requires manual reading against the saved page image. Character/script metrics alone are not an accuracy measure.

#### Existing raw extracted text (unchanged)

```text
[No text extracted]
```
#### Tesseract PSM 3

- Settings: language `asm`, OEM 1, PSM 3, 300 DPI
- Metrics: `{"characters": 3002, "alphabetic_characters": 1574, "assamese_block_letters": 1574, "assamese_block_letter_ratio": 1.0, "whitespace_words": 464, "replacement_characters": 0}`

```text
পুৰ্বজ্ঞানৰ সহায়ত অৰ্থৰ সংগঠন কৰিব পাৰে আৰু কোৱা কথাৰ নিহিতাৰ্থ বুজিব পাৰে, তাৰ ওপৰত গুৰুত্ব দিব লাগিব।

পঠন কেৱল পুথিগত কৌশল নহয়; ই এটা জীৱনজোৰা প্রক্ৰিয়া । পঠন হ’ল পঢ়ি লৈ তাৰ ওপৰত প্রতিক্রিয়া প্ৰকাশ
কৰা এক প্রক্ৰিয়া ৷ পঠনৰ অৰ্থ-সন্ধান (অৰ্থোদ্ধাৰ) কেৱল শব্দ আৰু বাক্যৰ অৰ্থ-সন্ধান (অৰ্থোদ্ধাৰ) তে সীমাবদ্ধ নহয়,
ই পাঠৰ সমগ্ৰতাটো নিহিত হৈ থাকে। কেতিয়াবা কেতিয়াবা আনকি পাঠটোত স্পষ্টভাৱে যি কথা কোৱা নহয় সেই কথাৰ
অৰ্থ বুজাটোও প্রয়োজনীয় হৈ পৰে। আমি এইটোও বুজা উচিত যে, প্রতিটো লিখনিৰে এক স্বকীয় প্রকাশভংগী থাকে
আৰু সেই প্রকাশভংগীক বুজিবলৈ পৰিচিত অৰ্থ গঠন সদায় সহায়ক হয়।

লিখন কৌশল শিকনৰ বাবে শিশুসকলে বিদ্যালয়লৈ আহি এটা প্রকৃত মুক্ত লিখন পৰিৱেশ পোৱা উচিত। লিখন
প্রক্ৰিয়াই তেতিয়াহে সাৰ্থকতা লাভ কৰে যেতিয়া শিশুসকলে নিজৰ ভাষা, কল্পনা, চিন্তা-ভাৱনা, আৱেগ-অনুভূতি আদি
নিজা দৃষ্টিভংগীৰে লিখিবলৈ স্বাধীনতা পায়। আনহাতে শিশুৱে কেৱল কৃষ্ণফলক, কিতাপ অথবা শিক্ষকে লিখি দিয়া
কথাবোৰহে অনুৰূপভাৱে লিখাৰ সলনি যাতে নিজৰ ভাষিক প্রকাশ আৰু সৃষ্টিশীল লিখনিৰে আত্মপ্ৰকাশৰ শৈলী বিকশিত
কৰাৰো সুবিধা লাভ কৰে তাক নিশ্চিত কৰা উচিত।

ছাত্ৰ-ছাত্ৰীসকলে নিজৰ পাঠ্যপুথিখন পঢ়িবলৈ শিকি, পাঠ্যপুথিৰ প্ৰতিটো পাঠৰ অনুশীলনত দিয়া প্রশ্নবোৰৰ উত্তৰ
লিখিব পৰাটোৱেই পঠন আৰু লিখনৰ একমাত্ৰ উদ্দেশ্য নহয়; ইয়াৰ লগে লগে যাতে তেওঁলোকে নিজৰ দৈনন্দিন
জীৱনত লিখা,পঢ়াৰ সঠিক ব্যৱহাৰ কৰিব পাৰে, পাঠৰ অন্তৰ্নিহিত সামাজিক আৰু সাংস্কৃতিক মূল্যবোধ সমূহক প্রতিফলিত
পাৰ্থক্যও অন্তৰ্ভুক্ত হোৱা উচিত। পঠন পদ্ধতি নিৰ্ভৰ কৰে পঠনৰ উদ্দেশ্য কি তাৰ ওপৰত। এখন বিজ্ঞাপন পঢ়া আৰু
এখন জাননী পঢ়া, সাধু পঢ়া আৰু কবিতা পঢ়াৰ পদ্ধতিৰ মাজত পাৰ্থক্য থাকে। লিখনৰ ক্ষেত্ৰটো এই কথাটো মহত্বপূৰ্ণ,
কিয়নো পাঠক কোন, কাৰ কাৰণে বা কাক উদ্দেশ্য কৰি আমি লিখিছোঁ, সেইটোও গুৰুত্বপূৰ্ণ । যদি কোনো গল্প বা কাহিনী
পঢ়ি তাত থকা চৰিত্ৰ আৰু ঘটনাক্ৰম সম্পৰ্কে গভীৰভাৱে চিন্তা কৰে, যেনে--- এইটো যদি হ’ল, কিয় হ’ল; কাহিনীত
এনেকুৱা কি আছে, যিটো যদি নহ’লহেঁতেন কাহিনী কোন ফালে গতি কৰিলেহেঁতেন ইত্যাদি ইত্যাদি৷ এইদৰে পাঠকৰ মনত
অনুসন্ধিৎ্সা জগাই তুলিব পৰাটোও লিখনিৰ এক উদ্দেশ্য । আমাৰ পঠন আৰু লিখনত বহুতো বিকল্প আছে, বহুতো স্তৰ
আছে আৰু প্রতিটো বিকল্প, প্রতিটো স্তৰেই গুৰুত্বপূৰ্ণ আৰু পৰস্পৰ সম্পৰ্কিত; এইবোৰে শ্ৰেণীত উপযুক্ত স্থান আৰু
মৰ্যাদা পোৱা উচিত।

প্রাথমিক স্তৰত শিশুসকলৰ পৰা আশা কৰা হয় যে, তেওঁলোকে কোৱা আৰু আনে লিখা কথাৰ সন্দৰ্ভত প্রতিক্রিয়া
প্রকাশ কৰিব পাৰে আৰু প্রশ্ন সুধিব পাৰে। শিশুৱে মনৰ ভাৱ প্রকাশৰ বাবে ব্যৱহাৰ কৰা ভাষাই এই কথাৰ প্রমাণ যে,
তেওঁলোকে নিজৰ ব্যৱহৃত ভাষাৰ ব্যাকৰণ জানে। কিন্তু ব্যাকৰণৰ সূত্ৰসমূহ বুজি পাবৰ বাবে তেওঁলোকে ব্যাকৰণৰ
বিভিন্ন দিশবোৰৰ বিষয়ে পাঠ্যপুথিৰ পাঠসমূহৰ জৰিয়তে অৱগত হোৱাতো প্রয়োজনীয় আৰু চাৰিওফালৰ পৰিবেশৰ
লগত জড়িত কৰি প্রয়োগ কৰাটোও অতি আৱশ্যক। ভাষাৰ বিভিন্ন ধৰণৰ প্ৰয়োগৰ প্রতি শিশুৰ মন আকৰ্ষণ কৰাৰ
প্রয়োজন, যাতে ভাষাৰ জটিলতাসমূহ ধৰিব পাৰে আৰু নিজৰ কথন শৈলীত তাক প্রয়োগ কৰিব পাৰে। ভাষা শিকন আৰু
শিক্ষন প্রক্ৰিয়া আৰু পৰিৱেশৰ ক্ষেত্ৰত এইটো লক্ষ্য ৰখা উচিত যে এটা শ্ৰেণীত প্রয়োগ কৰা প্রক্ৰিয়াটো পৰৱৰ্তী শ্ৰেণীৰ
বাবে ব্যৱহাৰ কৰিব পৰা যায়। শ্ৰেণী অনুসাৰে আকৰ্ষণীয় আৰু ৰুচি সন্মত বিষয়বস্তু প্রস্তুত কৰ উচিত, যিয়ে শিশুসকলক
অসমীয়া ভাষাৰ বিভিন্ন ৰূপ আৰু শৈলীৰ সৈতে পৰিচিত হ’বলৈ আৰু তাৰ প্রভাৱশালী প্ৰয়োগ বাস্তৱ জীৱনত প্রয়োগ
```

#### Tesseract PSM 6

- Settings: language `asm`, OEM 1, PSM 6, 300 DPI
- Metrics: `{"characters": 3006, "alphabetic_characters": 1575, "assamese_block_letters": 1575, "assamese_block_letter_ratio": 1.0, "whitespace_words": 466, "replacement_characters": 0}`

```text
পুৰ্বজ্ঞানৰ সহায়ত অৰ্থৰ সংগঠন কৰিব পাৰে আৰু কোৱা কথাৰ নিহিতাৰ্থ বুজিব পাৰে, তাৰ ওপৰত গুৰুত্ব দিব লাগিব।

পঠন কেৱল পুথিগত কৌশল নহয়; ই এটা জীৱনজোৰা প্রক্ৰিয়া । পঠন হ’ল পঢ়ি লৈ তাৰ ওপৰত প্রতিক্রিয়া প্ৰকাশ
কৰা এক প্রক্ৰিয়া ৷ পঠনৰ অৰ্থ-সন্ধান (অৰ্থোদ্ধাৰ) কেৱল শব্দ আৰু বাক্যৰ অৰ্থ-সন্ধান (অৰ্থোদ্ধাৰ) তে সীমাবদ্ধ নহয়,
ই পাঠৰ সমগ্ৰতাটো নিহিত হৈ থাকে। কেতিয়াবা কেতিয়াবা আনকি পাঠটোত স্পষ্টভাৱে যি কথা কোৱা নহয় সেই কথাৰ
অৰ্থ বুজাটোও প্রয়োজনীয় হৈ পৰে। আমি এইটোও বুজা উচিত যে, প্রতিটো লিখনিৰে এক স্বকীয় প্রকাশভংগী থাকে
আৰু সেই প্রকাশভংগীক বুজিবলৈ পৰিচিত অৰ্থ গঠন সদায় সহায়ক হয়।

লিখন কৌশল শিকনৰ বাবে শিশুসকলে বিদ্যালয়লৈ আহি এটা প্রকৃত মুক্ত লিখন পৰিৱেশ পোৱা উচিত। লিখন
প্রক্ৰিয়াই তেতিয়াহে সাৰ্থকতা লাভ কৰে যেতিয়া শিশুসকলে নিজৰ ভাষা, কল্পনা, চিন্তা-ভাৱনা, আৱেগ-অনুভূতি আদি
নিজা দৃষ্টিভংগীৰে লিখিবলৈ স্বাধীনতা পায়। আনহাতে শিশুৱে কেৱল কৃষ্ণফলক, কিতাপ অথবা শিক্ষকে লিখি দিয়া
কথাবোৰহে অনুৰূপভাৱে লিখাৰ সলনি যাতে নিজৰ ভাষিক প্রকাশ আৰু সৃষ্টিশীল লিখনিৰে আত্মপ্ৰকাশৰ শৈলী বিকশিত
কৰাৰো সুবিধা লাভ কৰে তাক নিশ্চিত কৰা উচিত।

ছাত্ৰ-ছাত্ৰীসকলে নিজৰ পাঠ্যপুথিখন পঢ়িবলৈ শিকি, পাঠ্যপুথিৰ প্ৰতিটো পাঠৰ অনুশীলনত দিয়া প্রশ্নবোৰৰ উত্তৰ
লিখিব পৰাটোৱেই পঠন আৰু লিখনৰ একমাত্ৰ উদ্দেশ্য নহয়; ইয়াৰ লগে লগে যাতে তেওঁলোকে নিজৰ দৈনন্দিন
জীৱনত লিখা,পঢ়াৰ সঠিক ব্যৱহাৰ কৰিব পাৰে, পাঠৰ অন্তৰ্নিহিত সামাজিক আৰু সাংস্কৃতিক মূল্যবোধ সমূহক প্রতিফলিত
পাৰ্থক্যও অন্তৰ্ভুক্ত হোৱা উচিত। পঠন পদ্ধতি নিৰ্ভৰ কৰে পঠনৰ উদ্দেশ্য কি তাৰ ওপৰত। এখন বিজ্ঞাপন পঢ়া আৰু
এখন জাননী পঢ়া, সাধু পঢ়া আৰু কবিতা পঢ়াৰ পদ্ধতিৰ মাজত পাৰ্থক্য থাকে। লিখনৰ ক্ষেত্ৰটো এই কথাটো মহত্বপূৰ্ণ,
কিয়নো পাঠক কোন, কাৰ কাৰণে বা কাক উদ্দেশ্য কৰি আমি লিখিছোঁ, সেইটোও গুৰুত্বপূৰ্ণ । যদি কোনো গল্প বা কাহিনী
পঢ়ি তাত থকা চৰিত্ৰ আৰু ঘটনাক্ৰম সম্পৰ্কে গভীৰভাৱে চিন্তা কৰে, যেনে--- এইটো যদি হ’ল, কিয় হ’ল; কাহিনীত
এনেকুৱা কি আছে, যিটো যদি নহ’লহেঁতেন কাহিনী কোন ফালে গতি কৰিলেহেঁতেন ইত্যাদি ইত্যাদি । এইদৰে পাঠকৰ মনত
অনুসন্ধিৎ্সা জগাই তুলিব পৰাটোও লিখনিৰ এক উদ্দেশ্য । আমাৰ পঠন আৰু লিখনত বহুতো বিকল্প আছে, বহুতো স্তৰ
আছে আৰু প্রতিটো বিকল্প, প্ৰতিটো স্তৰেই গুৰুত্বপূৰ্ণ আৰু পৰস্পৰ সম্পৰ্কিত; এইবোৰে শ্ৰেণীত উপযুক্ত স্থান আৰু
মৰ্যাদা পোৱা উচিত।

প্রাথমিক স্তৰত শিশুসকলৰ পৰা আশ৷ কৰা হয় যে, তেওঁলোকে কোৱা আৰু আনে লিখা কথাৰ সন্দৰ্ভত প্রতিক্ৰিয়া
প্রকাশ কৰিব পাৰে আৰু প্রশ্ন সুধিব পাৰে। শিশুৱে মনৰ ভাৱ প্রকাশৰ বাবে ব্যৱহাৰ কৰা ভাষাই এই কথাৰ প্রমাণ যে,
তেওঁলোকে নিজৰ ব্যৱহৃত ভাষাৰ ব্যাকৰণ জানে। কিন্তু ব্যাকৰণৰ সূত্ৰসমূহ বুজি পাবৰ বাবে তেওঁলোকে ব্যাকৰণৰ
বিভিন্ন দিশবোৰৰ বিষয়ে পাঠ্যপুথিৰ পাঠসমূহৰ জৰিয়তে অৱগত হোৱাতো প্রয়োজনীয় আৰু চাৰিওফালৰ পৰিবেশৰ
লগত জড়িত কৰি প্রয়োগ কৰাটোও অতি আৱশ্যক। ভাষাৰ বিভিন্ন ধৰণৰ প্ৰয়োগৰ প্রতি শিশুৰ মন আকৰ্ষণ কৰাৰ
প্রয়োজন, যাতে ভাষাৰ জটিলতাসমূহ ধৰিব পাৰে আৰু নিজৰ কথন শৈলীত তাক প্রয়োগ কৰিব পাৰে। ভাষা শিকন আৰু
শিক্ষন প্রক্ৰিয়া আৰু পৰিৱেশৰ ক্ষেত্ৰত এইটো লক্ষ্য ৰখা উচিত যে এটা শ্ৰেণীত প্রয়োগ কৰা প্রক্ৰিয়াটো পৰৱৰ্তী শ্ৰেণীৰ
বাবে ব্যৱহাৰ কৰিব পৰা যায়। শ্ৰেণী অনুসাৰে আকৰ্ষণীয় আৰু ৰুচি সন্মত বিষয়বস্তু প্রস্তুত কৰ উচিত, যিয়ে শিশুসকলক
অসমীয়া ভাষাৰ বিভিন্ন ৰূপ আৰু শৈলীৰ সৈতে পৰিচিত হ’বলৈ আৰু তাৰ প্রভাৱশালী প্রয়োগ বাস্তৱ জীৱনত প্রয়োগ

ৰ
```

#### Tesseract PSM 11

- Settings: language `asm`, OEM 1, PSM 11, 300 DPI
- Metrics: `{"characters": 3265, "alphabetic_characters": 1665, "assamese_block_letters": 1665, "assamese_block_letter_ratio": 1.0, "whitespace_words": 505, "replacement_characters": 0}`

```text
পূৰ্বজ্ঞানৰ সহায়ত অৰ্থৰ সংগঠন কৰিব পাৰে আৰু কোৱা কথাৰ নিহিতাৰ্থ বুজিব পাৰে, তাৰ ওপৰত গুৰুত্ব দিব লাগিব।

পঠন কেৱল পুথিগত কৌশল নহয়; ই এটা জীৱনজোৰা প্রক্ৰিয়া । পঠন হ’ল পঢ়ি লৈ তাৰ ওপৰত প্ৰতিক্ৰিয়া প্রকাশ

কৰা এক প্রক্ৰিয়া। পঠনৰ অৰ্থ-সন্ধান (অৰ্থোদ্ধাৰ) কেৱল শব্দ আৰু বাক্যৰ অৰ্থ-সন্ধান (অৰ্থোদ্ধাৰ) তে সীমাবদ্ধ নহয়,

ই পাঠৰ সমগ্ৰতাটো নিহিত হৈ থাকে। কেতিয়াবা কেতিয়াবা আনকি পাঠটোত স্পষ্টভাৱে যি কথা কোৱা নহয় সেই কথাৰ

অৰ্থ বুজাটোও প্রয়োজনীয় হৈ পৰে। আমি এইটোও বুজা উচিত যে, প্রতিটো লিখনিৰে এক স্বকীয় প্রকাশভংগী থাকে

আৰু সেই প্রকাশভংগীক বুজিবলৈ পৰিচিত অৰ্থ গঠন সদায় সহায়ক হয়।

লিখন কৌশল শিকনৰ বাবে শিশুসকলে বিদ্যালয়লৈ আহি এটা প্রকৃত মুক্ত লিখন পৰিৱেশ পোৱা উচিত। লিখন

প্রক্ৰিয়াই তেতিয়াহে সাৰ্থকতা লাভ কৰে যেতিয়া শিশুসকলে নিজৰ ভাষা, কল্পনা, চিন্তা-ভাৱনা, আৱেগ-অনুভূতি আদি

নিজা দৃষ্টিভংগীৰে লিখিবলৈ স্বাধীনতা পায়। আনহাতে শিশুৱে কেৱল কৃষ্ণফলক, কিতাপ অথবা শিক্ষকে লিখি দিয়া

কথাবোৰহে অনুৰূপভাৱে লিখাৰ সলনি যাতে নিজৰ ভাষিক প্রকাশ আৰু সৃষ্টিশীল লিখনিৰে আত্মপ্ৰকাশৰ শৈলী বিকশিত

কৰাৰো সুবিধা লাভ কৰে তাক নিশ্চিত কৰা উচিত।

ছাত্ৰ-ছাত্ৰীসকলে নিজৰ পাঠ্যপুথিখন পঢ়িবলৈ শিকি, পাঠ্যপুথিৰ প্ৰতিটো পাঠৰ অনুশীলনত দিয়া প্রশ্নবোৰৰ উত্তৰ

লিখিব পৰাটোৱেই পঠন আৰু লিখনৰ একমাত্ৰ উল্দেশ্য নহয়; ইয়াৰ লগে লগে যাতে তেওঁলোকে নিজৰ দৈনন্দিন

জীৱনত লিখা,পঢ়াৰ সঠিক ব্যৱহাৰ কৰিব পাৰে, পাঠৰ অন্তৰ্নিহিত সামাজিক আৰু সাংস্কৃতিক মূল্যবোধ সমূহক প্রতিফলিত

কৰিব পাৰে, সেয়া নিশ্চিত কৰিব লাগে। পঠন আৰু লিখন প্রক্ৰিয়াত উদ্দেশ্য অনুযায়ী পঢ়া আৰু লিখাৰ পদ্ধতিৰ

পাৰ্থক্যও অন্তৰ্ভুক্ত হোৱা উচিত। পঠন পদ্ধতি নিৰ্ভৰ কৰে পঠনৰ উদ্দেশ্য কি তাৰ ওপৰত। এখন বিজ্ঞাপন পঢ়া আৰু

এখন জাননী পঢ়া, সাধু পঢ়া আৰু কবিতা পঢ়াৰ পদ্ধতিৰ মাজত পাৰ্থক্য থাকে। লিখনৰ ক্ষেত্ৰটো এই কথাটো মহত্বপূৰ্ণ,

কিয়নো পাঠক কোন, কাৰ কাৰণে বা কাক উদ্দেশ্য কৰি আমি লিখিছোঁ, সেইটোও গুৰুত্বপূৰ্ণ । যদি কোনো গল্প বা কাহিনী

পঢ়ি তাত থকা চৰিত্ৰ আৰু ঘটনাক্ৰম সম্পৰ্কে গভীৰভাৱে চিন্তা কৰে, যেনে--- এইটো যদি হ’ল, কিয় হ’ল; কাহিনীত

এনেকুৱা কি আছে, যিটো যদি নহ’লহেঁতেন কাহিনী কোন ফালে গতি কৰিলেহেঁতেন ইত্যাদি ইত্যাদি৷ এইদৰে পাঠকৰ মনত

অনুসন্ধিৎ্সা জগাই তুলিব পৰাটোও লিখনিৰ এক উদ্দেশ্য । আমাৰ পঠন আৰু লিখনত বহুতো বিকল্প আছে, বহুতো স্তৰ

আছে আৰু প্রতিটো বিকল্প, প্রতিটো স্তৰেই গুৰুত্বপূৰ্ণ আৰু পৰস্পৰ সম্পৰ্কিত; এইবোৰে শ্ৰেণীত উপযুক্ত স্থান আৰু

মৰ্যাদা পোৱা উচিত।

প্ৰাথমিক স্তৰত শিঙুসকলৰ পৰা আশ৷ কৰা হয় যে, তেওঁলোকে কোৱা আৰু আনে লিখা কথাৰ সন্দৰ্ভত প্ৰতিক্ৰিয়া

প্রকাশ কৰিব পাৰে আৰু প্রশ্ন সুধিব পাৰে। শিশুৱে মনৰ ভাৱ প্রকাশৰ বাবে ব্যৱহাৰ কৰা ভাষাই এই কথাৰ প্রমাণ যে,

তেওঁলোকে নিজৰ ব্যৱহৃত ভাষাৰ ব্যাকৰণ জানে। কিন্তু ব্যাকৰণৰ সূত্ৰসমূহ বুজি পাবৰ বাবে তেওঁলোকে ব্যাকৰণৰ

বিভিন্ন দিশবোৰৰ বিষয়ে পাঠ্যপুথিৰ পাঠসমূহৰ জৰিয়তে অৱগত হোৱাতো প্রয়োজনীয় আৰু চাৰিওফালৰ পৰিবেশৰ

লগত জড়িত কৰি প্রয়োগ কৰাটোও অতি আৱশ্যক। ভাষাৰ বিভিন্ন ধৰণৰ প্রয়োগৰ প্রতি শিশুৰ মন আকৰ্ষণ কৰাৰ

প্রয়োজন, যাতে ভাষাৰ জটিলতাসমূহ ধৰিব পাৰে আৰু নিজৰ কথন শৈলীত তাক প্রয়োগ কৰিব পাৰে। ভাষা শিকন আৰু

শিক্ষন প্রক্ৰিয়া আৰু পৰিৱেশৰ ক্ষেত্ৰত এইটো লক্ষ্য ৰখা উচিত যে এটা শ্ৰেণীত প্রয়োগ কৰা প্ৰক্ৰিয়াটো পৰৱৰ্তী শ্ৰেণীৰ

বাবে ব্যৱহাৰ কৰিব পৰা যায়। শ্ৰেণী অনুসাৰে আকৰ্ষণীয় আৰু ৰুচি সন্মত বিষয়বস্তু প্রস্তুত কৰ উচিত, যিয়ে শিশুসকলক

অসমীয়া ভাষাৰ বিভিন্ন ৰূপ আৰু শৈলীৰ সৈতে পৰিচিত হ’বলৈ আৰু তাৰ প্রভাৱশালী প্রয়োগ বাস্তৱ জীৱনত প্রয়োগ

ৰ্‌

_

23% 72!

কু

ফু

ৰি

আমি বিদ্যালয়লৈ

]}

ৰ্্জ

)

তে

[৷

কু

যাবলৈ ভাল পাও। জ্ষী

ট্পৰ্ত্

“স্বৰ

ঢ়

ঞ্,

র্ব্জ্া

এড ্্ই(
```

## Limitations and review

- Assam and Bengali share the Unicode block measured here. An Assamese-block count does not prove that the OCR language is Assamese, nor that the text is readable or faithful.
- Tesseract has only the `asm` language pack installed; English/Bengali packs were not used or fetched.
- Inspect the saved PNG alongside each exact OCR output. Mark page transcription quality manually before using any OCR result.
- OCR output is diagnostic only. This report does not clean, merge, or replace raw extracted text.
- The sample is diagnostic, not representative proof for every page or every PDF. Review rights before any future training use.
