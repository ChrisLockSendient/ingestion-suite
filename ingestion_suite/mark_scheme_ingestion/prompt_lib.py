clean_up_markdown_prompt = """
# Role and Objective
You are an expert data-cleaning agent. You are provided with a markdown document that contains the OCR of a mark scheme document for a high school assessment.
Your job is to clean up the markdown so that it is easier to extract structured data from. This entails removing any trailing and leading information that is not part of the actual mark schemes.

# Instructions
1. Read the markdown document.
2. Remove any trailing and leading information that is not part of the actual mark schemes.
3. Clean up tables in the markdown, trying not to remove any important information.
4. Maintain the columns of any markdown tables.
5. If tables are seperate in the markdown, attempt to merge them into a single unified table but only if the tables have the same (or similar) columns.
6. Return the cleaned up markdown.

# Output Format
Return the cleaned up markdown as a string with no extra text or comments.

# Examples

Examples of inputs and outputs are provided below, with inputs to you in <input_1> and <input_2> tags and what you would return in <output_1> and <output_2> tags.

## Example 1
<input_1>
# AGA 5

## GCSE BIOLOGY 8461/1F

Paper 1 Foundation Tier
Mark scheme
June 2023
Version: 1.0 Final
![image_1](image_1)

---

Mark schemes are prepared by the Lead Assessment Writer and considered, together with the relevant questions, by a panel of subject teachers. This mark scheme includes any amendments made at the standardisation events which all associates participate in
and is the scheme which was used by them in this examination. The standardisation process ensures that the mark scheme covers the students' responses to questions and that every associate understands and applies it in the same correct way. As preparation for standardisation each associate analyses a number of students' scripts. Alternative answers not already covered by the mark scheme are discussed and legislated for. If, after the standardisation process, associates encounter unusual answers which have not been raised they are required to refer these to the Lead Examiner.

# Information to Examiners

## 1. General

The mark scheme for each question shows:

- the marks available for each part of the question
- the total marks available for the question
- the typical answer or answers which are expected
- extra information to help the examiner make their judgement
- the Assessment Objectives and specification content that each question is intended to cover.

The extra information is aligned to the appropriate answer in the left-hand part of the mark scheme and should only be applied
to that item in the mark scheme.

At the beginning of a part of a question a reminder may be given, for example: where consequential marking needs to be considered in a calculation; or the answer may be on the diagram or at a different place on the script.

In general the right-hand side of the mark scheme is there to provide those extra details which confuse the main part of the mark scheme yet may be helpful in ensuring that marking is straightforward and consistent (for example, a scientifically correct
answer that could not reasonably be expected from a student's knowledge of the specification).

## 2. Emboldening and underlining

2.1 In a list of acceptable answers where more than one mark is available 'any two from' is used, with the number of marks emboldened. Each of the following bullet points is a potential mark.
2.2 A bold and is used to indicate that both parts of the answer are required to award the mark.
2.3 Alternative answers acceptable for a mark are indicated by the use of or.

Alternative words in the mark scheme are shown by a solidus eg allow smooth / free movement.
2.4 Any wording that is underlined is essential for the marking point to be awarded.

| Question | Answers | Mark | AO / <br> Spec Ref. |
| :--: | :--: | :--: | :--: |
| 01.1 | Level 3: Relevant points (reasons / causes) are identified, given in detail and logically linked to form a clear account. | $5-6$ | $\\\\begin{gathered} \\\\text { AO1 } \\\\\\\\ \\\\text { AO2 } \\\\end{gathered}$ |
|  | Level 2: Relevant points (reasons / causes) are identified, and there are attempts at logical linking. The resulting account is not fully clear. | $3-4$ | $\\\\begin{aligned} & 4.2 .2 .4 \\\\\\\\ & 4.4 .2 .1 \\\\\\\\ & 4.4 .2 .2 \\\\end{aligned}$ |
|  | Level 1: Points are identified and stated simply, but their relevance is not clear and there is no attempt at logical linking. | $1-2$ |  |
|  | No relevant content. | 0 |  |
|  | Indicative content: <br> - reduced blood flow to heart (muscle / tissue / cells) <br> - (so) less oxygen to heart (muscle
/ tissue / cells) <br> - (so) less glucose to heart (muscle / tissue / cells) <br> - (so) less (aerobic) respiration (in heart
/ body cells) <br> - (more) anaerobic respiration <br> - (so) less energy (released) <br> - (so) less muscle contraction <br> - (so) less blood / oxygen / glucose around the body (from heart) or slower flow of blood / oxygen / glucose to body (from heart) <br> - less carbon dioxide removed from body (muscle / tissue / cells) <br> - (resulting in) breathlessness <br> - (resulting in) tiredness <br> - (anaerobic respiration causes) production of lactic acid <br> - (build-up of lactic acid) causes muscle fatigue / pain or chest pain |  |  |
|  | For Level 3, students must explain the effect of reduced oxygen / glucose on respiration or energy release and its consequence |  |  |

| Question | Answers | Extra information | Mark | $\\\\begin{gathered} \\\\text { AO / } \\\\\\\\ \\\\text { Spec Ref. } \\\\end{gathered}$ |
| :--: | :--: | :--: | :--: | :--: |
| 01.2 | any one pair from: <br> - (insert) stent(s) <br> (to) open (coronary) artery <br> - (prescribe) statins (1) <br> (to)
reduce (blood) <br> cholesterol (1) <br> - heart (and lung) transplant (1) <br> (to) replace the diseased <br> heart with a healthy heart (1) <br> - use an artificial heart (1) <br> (to) keep the patient alive <br> while waiting for a transplant <br> (1) <br> - (artery / heart) bypass (1) <br> (to) divert blood around the <br> blockage (1) | mark as a pair <br> allow description <br> ignore unblock (coronary) artery <br> allow to slow down the rate of <br> fatty material deposit <br> allow (artificial heart) <br> pumps blood around the <br> body in place of the heart <br> allow description | 1 <br> 1 | $\\\\begin{gathered} \\\\text { AO1 } \\\\\\\\ 4.2 .2 .4 \\\\end{gathered}$ |
| Total Question 7 |  |  | 19 |  |

| Question | Answers | Extra information | Mark | AO / <br> Spec Ref. |
| :--: | :--: | :--: | :--: | :--: |
| 01.3 | amino acids |  | 1 | $\\\\begin{aligned} & \\\\text { AO1 } \\\\\\\\ & 4.2 .2 .1 \\\\end{aligned}$ |
</input_1>
<output_1>
| Question | Answers                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   | Extra information                                                                                                                                                                                                                                               |         Mark        |                    AO / Spec Ref.                   |
| :------: | :------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | :-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | :-----------------: | :-------------------------------------------------: |
|   01.1   | **Level 3:** Relevant points (reasons / causes) are identified, given in detail and logically linked to form a clear account. <br><br> **Level 2:** Relevant points (reasons / causes) are identified, and there are attempts at logical linking. The resulting account is not fully clear. <br><br> **Level 1:** Points are identified and stated simply, but their relevance is not clear and there is no attempt at logical linking. <br><br> **No relevant content.** <br><br> **Indicative content:** <br> • reduced blood flow to heart (muscle / tissue / cells) <br> • less oxygen to heart (muscle / tissue / cells) <br> • less glucose to heart (muscle / tissue / cells) <br> • less (aerobic) respiration (in heart / body cells) <br> • more anaerobic respiration <br> • less energy (released) <br> • less muscle contraction <br> • less blood / oxygen / glucose around the body (from heart) or slower flow of blood / oxygen / glucose to body (from heart) <br> • less carbon dioxide removed from body (muscle / tissue / cells) <br> • breathlessness <br> • tiredness <br> • production of lactic acid (anaerobic respiration) <br> • build-up of lactic acid causes muscle fatigue / pain or chest pain <br><br> For Level 3, students must explain the effect of reduced oxygen / glucose on respiration or energy release and its consequence. |                                                                                                                                                                                                                                                                 | 5–6 / 3–4 / 1–2 / 0 | AO1 <br> AO2 <br> 4.2.2.4 <br> 4.4.2.1 <br> 4.4.2.2 |
|   01.2   | Any **one pair** from: <br> • (insert) stent(s) — (to) open (coronary) artery <br> • (prescribe) statins (1) — (to) reduce (blood) cholesterol (1) <br> • heart (and lung) transplant (1) — (to) replace the diseased heart with a healthy heart (1) <br> • use an artificial heart (1) — (to) keep the patient alive while waiting for a transplant (1) <br> • (artery / heart) bypass (1) — (to) divert blood around the blockage (1)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   | • Mark as a pair <br> • Allow description <br> • Ignore "unblock (coronary) artery" <br> • Allow "to slow down the rate of fatty material deposit" <br> • Allow "(artificial heart) pumps blood around the body in place of the heart" <br> • Allow description |          1          |                   AO1 <br> 4.2.2.4                  |
|   01.3   | amino acids                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               |                                                                                                                                                                                                                                                                 |          1          |                   AO1 <br> 4.2.2.1                  |
</output_1>

## Example 2
<input_2>
# AGA

## GCSE GEOGRAPHY 8035/3

Paper 3 Geographical Applications
Mark scheme
June 2020
Version: 1.0 Final Mark Scheme

---

Mark schemes are prepared by the Lead Assessment Writer and considered, together with the relevant questions, by a panel of subject teachers. This mark scheme includes any amendments made at the standardisation events which all associates participate in
and is the scheme which was used by them in this examination. The standardisation process ensures that the mark scheme covers the students' responses to questions and that every associate understands and applies it in the same correct way. As preparation for standardisation each associate analyses a number of students' scripts. Alternative answers not already covered by the mark scheme are discussed and legislated for. If, after the standardisation process, associates encounter unusual answers which have not been raised they are required to refer these to the Lead Examiner.

It must be stressed that a mark scheme is a working document, in many cases further developed and expanded on the basis of students' reactions to a particular paper. Assumptions about future mark schemes on the basis of one year's document should be avoided; whilst the guiding principles of assessment remain constant, details will change, depending on the content of a particular examination paper.

Further copies of this mark scheme are available from aqa.org.uk

# Copyright information

AQA retains the copyright on all its publications. However, registered schools/colleges for AQA are permitted to copy material
from this booklet for their own internal use, with the following important exception: AQA cannot give permission to schools/colleges to photocopy any material that is acknowledged to a third party even for internal use within the centre.

Copyright © 2020 AQA and its licensors. All rights reserved.

---

# Point marked questions marking instructions

The mark scheme will state the correct answer or a range of possible answers, although these may not be exhaustive. It may indicate how a second mark is awarded for a second point or developed idea. It may give an indication of unacceptable answers. Each mark should be shown by placing a tick where credit is given. The number of ticks must equal the mark awarded. Do not use crosses to indicate answers that are incorrect.

## Level of response marking instructions

Level of response mark schemes are broken down into levels, each of which has a descriptor. The descriptor is linked to the Assessment Objective(s) being addressed. The descriptor for the level shows the average performance for the level.

Before you apply the mark scheme to a student's answer read through the answer and annotate it (as instructed) to show the qualities that are being looked for. You can then apply the mark scheme. You should read the whole answer before awarding marks on
levels response questions.

## Step 1 Determine a level

Descriptors for the level indicate the different qualities that might be seen in the student's answer for that level. When assigning a level you should look at the overall quality of the answer and not look to pick holes in small and specific parts of the answer where the student has not performed quite as well as the rest. If the answer covers different aspects of different levels of the mark scheme you should use a best fit approach for defining the level and then use the variability of the response to help decide the mark within the level, ie if the response is predominantly Level 2 with a small amount of Level 3 material it would be placed in Level 2 but be awarded a mark near the top of the level because of the Level 3 content. For instance, in a
9 mark question with three levels of response, an answer may demonstrate thorough knowledge and understanding (AO1 and AO2) but fail to respond to command words such as assess or evaluate (AO3). The script could still access Level 2 marks. Note that the
mark scheme is not progressive in the sense that students don't have to fulfil all the requirements of Level 1 in order to access Level 2.

## Step 2 Determine a mark

Once you have assigned a level you need to decide on the mark. The descriptors on how to allocate marks can help with this. The exemplar materials used during standardisation will also help. There will generally be an answer in the standardising materials which will correspond with each level of the mark scheme. This answer will have been awarded a mark by the Lead Examiner. You can compare the student's answer with the example to determine if it is the same standard, better or worse than the example. You can then use this to allocate a mark for the answer based on the Lead Examiner's mark on the example. You may well need to read back through the answer as you apply the mark scheme to clarify points and assure yourself that the level and the mark are
appropriate.

Indicative content in the mark scheme is provided as a guide for examiners. It is not intended to be exhaustive and you must credit other valid points. Students do not have to cover all of the points mentioned in the indicative content to reach the highest level of the mark scheme.

An answer which contains nothing of relevance to the question must be awarded no marks.


| Qu | Pt | Marking Guidance | Total marks |
| :--: | :--: | :--: | :--: |
| 01 | 1 | In which year were global urban and rural populations the same? <br> One mark for correct answer: <br> B: 2007 <br>
No credit if two or more answers are shaded. <br> AO4 - 1 mark | 1 |
| 01 | 2 | Which of the following statements is correct? <br> One mark for correct answer: <br> A: Latin America/Caribbean is predicted to double its \\\\% urban population between 1950-2030 <br> No credit if two or more answers are shaded. <br> AO4 - 1 mark | 1 |

---

| 01 | 3 | Explain the link between economic development and urbanisation. |  | 4 |
| :--: | :--: | :--: | :--: | :--: |
|  |  | Level | Marks | Description |
|  |  | $\\\\begin{gathered} 2 \\\\\\\\ \\\\text { (Clear) } \\\\end{gathered}$ | $3-4$ | AO2 - Shows a clear understanding of the concepts of economic development and urbanisation. <br> AO2 - Demonstrates a clear awareness of the relationship between economic development and urbanisation. |
|  |  | $\\\\begin{gathered} 1 \\\\\\\\ \\\\text { (Basic) } \\\\end{gathered}$ | $1-2$ | AO2 - Limited understanding of the concepts of economic development and urbanisation. <br> AO2 - A limited appreciation of the link between economic development and urbanisation.
|
|  |  |  | 0 | No relevant content. |

- Level 2 (clear) - identifies the link between economic development and urbanisation and suggests reasons for the relationship which identify the specific socio-economic facilities/opportunities that exist in urban areas and suggest that these are often 'core' growth areas.
- Level 1 (basic) - identifies the link between economic development and urbanisation and makes basic, unqualified observations (jobs and money/socio-economic opportunities/facilities) that exist in urban areas (without elaboration).


# Indicative content

- There is a positive relationship between economic development and urbanisation.
- The relationship is emphasised by the cluster of very poor countries that also have lower rates of urban populations.
- Urban areas are often core areas where industry and infrastructure develops. This creates opportunities for a range of both skilled and unskilled jobs.
- Urban growth creates opportunity for unskilled/informal employment.
- There is a greater opportunity for education and job-related training in urban/industrial areas.
- Students may consider cumulative causation/the multiplier effect.

AO2 - 4 marks

---

| 01 | 4 | Suggest two reasons why estimates of future urban population may not be accurate. <br> No credit for simply saying "it is only a prediction" <br> $2 \\\\times 1$ marks <br> Any reasonable answers, which might include; <br> - Difficulty in actually counting current numbers (1) <br> - Economic growth may be faster/slower (1) <br> - Birth rates may increase/fall (1) <br> -
Death rates may increase/decrease(1) <br> - Conditions in rural areas might improve (1) <br> - Natural disasters/climate change related factors (drought) (1). <br> - Original data used for prediction may not be accurate (1). <br> - Idea of rapid change leading to inaccuracy(1). <br> AO2 - 2 marks | 2 |
| :--: | :--: | :--: | :--: |
| 01 | 5 | Suggest one challenge that urbanisation creates for rural areas. <br> 1 mark for identification of appropriate point; $2^{\\\\text {nd }}$ mark for developed idea <br> - Decline of rural communities/ Lack of investment in rural areas (1) <br> - Loss of working population (1) leads to agricultural/industrial decline(1)(d) <br> - Imbalance in the population structure (1) <br> - It is mostly younger people who migrate (1) so the population has a disproportionate number of older people (dependency idea) (1)(d) <br> - Lack of investment/growing wealth gap between urban/rural areas. (1) because most investment goes to urban areas (1) <br> - Because most of the business development/income is in urban areas(1) the wealth gap between rural and urban areas grows. (1)(d) | 2 |

</input_2>
<output_2>
|  Qu |  Pt | Marking Guidance                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            | Total marks |
| :-: | :-: | :---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | :---------: |
|  01 |  1  | In which year were global urban and rural populations the same? <br> **Correct answer:** B: 2007 <br> • No credit if two or more answers are shaded. <br> **AO4 – 1 mark**                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  |      1      |
|  01 |  2  | Which of the following statements is correct? <br> **Correct answer:** A: Latin America/Caribbean is predicted to double its % urban population between 1950-2030 <br> • No credit if two or more answers are shaded. <br> **AO4 – 1 mark**                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 |      1      |
|  01 |  3  | Explain the link between economic development and urbanisation. <br> **Level 2 (clear):** <br> • Identifies the link between economic development and urbanisation. <br> • Suggests reasons for the relationship, identifying specific socio-economic facilities/opportunities in urban areas. <br> • Recognises urban areas as core growth areas. <br> **Level 1 (basic):** <br> • Identifies the link but makes basic, unqualified observations (e.g., jobs, money, socio-economic opportunities) without elaboration. <br> **Indicative content:** <br> • Positive relationship between economic development and urbanisation. <br> • Poorer countries have lower urban populations. <br> • Urban areas are core industrial/infrastructure hubs. <br> • Opportunities for skilled/unskilled/informal employment. <br> • Greater access to education and training. <br> • Consideration of cumulative causation/multiplier effect. <br> **AO2 – 4 marks** |      4      |
|  01 |  4  | Suggest two reasons why estimates of future urban population may not be accurate. <br> **No credit** for simply saying "it is only a prediction." <br> **2 × 1 marks** for any reasonable answer, e.g.: <br> • Difficulty counting current numbers <br> • Economic growth rate variability <br> • Birth/death rate changes <br> • Rural conditions improving <br> • Natural disasters/climate factors (drought) <br> • Original data inaccuracies <br> • Rapid change leading to inaccuracy <br> **AO2 – 2 marks**                                                                                                                                                                                                                                                                                                                                                                                                                                          |      2      |
|  01 |  5  | Suggest one challenge that urbanisation creates for rural areas. <br> **1 mark** for identification; **1 mark** for development. <br> Examples: <br> • Decline of rural communities/lack of investment <br> • Loss of working population leads to agricultural/industrial decline <br> • Imbalance in population structure <br> • Youth migration leaves ageing population/dependency ratio issues <br> • Wealth gap grows as investment focuses on urban areas <br> **Total 2 marks**                                                                                                                                                                                                                                                                                                                                                                                                                                                                      |      2      |
</output_2>

# Important Notes
 - Do not add any extra text or comments to the markdown.
 - Do not remove any important information from the markdown.
 - Do not miss any of the mark scheme.
 - Ensure tables are valid markdown.
"""


extract_mark_schemes_from_document_prompt="""
Your task:
Extract all the mark schemes for all the questions from the document into markdown table format without modifying the content of the mark schemes.

Rules:
Where possible, provide just one table with all of the mark schemes in. If not possible then provide a table for each question's mark scheme.
Do not include any trailing commas, or commentary.
Do not use fenced code blocks (triple backticks) in the markdown.

Example outputs:
<output_1>
| Question | Answers                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   | Extra information                                                                                                                                                                                                                                               |         Mark        |                    AO / Spec Ref.                   |
| :------: | :------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | :-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | :-----------------: | :-------------------------------------------------: |
|   01.1   | **Level 3:** Relevant points (reasons / causes) are identified, given in detail and logically linked to form a clear account. <br><br> **Level 2:** Relevant points (reasons / causes) are identified, and there are attempts at logical linking. The resulting account is not fully clear. <br><br> **Level 1:** Points are identified and stated simply, but their relevance is not clear and there is no attempt at logical linking. <br><br> **No relevant content.** <br><br> **Indicative content:** <br> • reduced blood flow to heart (muscle / tissue / cells) <br> • less oxygen to heart (muscle / tissue / cells) <br> • less glucose to heart (muscle / tissue / cells) <br> • less (aerobic) respiration (in heart / body cells) <br> • more anaerobic respiration <br> • less energy (released) <br> • less muscle contraction <br> • less blood / oxygen / glucose around the body (from heart) or slower flow of blood / oxygen / glucose to body (from heart) <br> • less carbon dioxide removed from body (muscle / tissue / cells) <br> • breathlessness <br> • tiredness <br> • production of lactic acid (anaerobic respiration) <br> • build-up of lactic acid causes muscle fatigue / pain or chest pain <br><br> For Level 3, students must explain the effect of reduced oxygen / glucose on respiration or energy release and its consequence. |                                                                                                                                                                                                                                                                 | 5–6 / 3–4 / 1–2 / 0 | AO1 <br> AO2 <br> 4.2.2.4 <br> 4.4.2.1 <br> 4.4.2.2 |
|   01.2   | Any **one pair** from: <br> • (insert) stent(s) — (to) open (coronary) artery <br> • (prescribe) statins (1) — (to) reduce (blood) cholesterol (1) <br> • heart (and lung) transplant (1) — (to) replace the diseased heart with a healthy heart (1) <br> • use an artificial heart (1) — (to) keep the patient alive while waiting for a transplant (1) <br> • (artery / heart) bypass (1) — (to) divert blood around the blockage (1)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   | • Mark as a pair <br> • Allow description <br> • Ignore "unblock (coronary) artery" <br> • Allow "to slow down the rate of fatty material deposit" <br> • Allow "(artificial heart) pumps blood around the body in place of the heart" <br> • Allow description |          1          |                   AO1 <br> 4.2.2.4                  |
|   01.3   | amino acids                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               |                                                                                                                                                                                                                                                                 |          1          |                   AO1 <br> 4.2.2.1                  |
</output_1>

<output_2>
|  Qu |  Pt | Marking Guidance                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            | Total marks |
| :-: | :-: | :---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | :---------: |
|  01 |  1  | In which year were global urban and rural populations the same? <br> **Correct answer:** B: 2007 <br> • No credit if two or more answers are shaded. <br> **AO4 – 1 mark**                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  |      1      |
|  01 |  2  | Which of the following statements is correct? <br> **Correct answer:** A: Latin America/Caribbean is predicted to double its % urban population between 1950-2030 <br> • No credit if two or more answers are shaded. <br> **AO4 – 1 mark**                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 |      1      |
|  01 |  3  | Explain the link between economic development and urbanisation. <br> **Level 2 (clear):** <br> • Identifies the link between economic development and urbanisation. <br> • Suggests reasons for the relationship, identifying specific socio-economic facilities/opportunities in urban areas. <br> • Recognises urban areas as core growth areas. <br> **Level 1 (basic):** <br> • Identifies the link but makes basic, unqualified observations (e.g., jobs, money, socio-economic opportunities) without elaboration. <br> **Indicative content:** <br> • Positive relationship between economic development and urbanisation. <br> • Poorer countries have lower urban populations. <br> • Urban areas are core industrial/infrastructure hubs. <br> • Opportunities for skilled/unskilled/informal employment. <br> • Greater access to education and training. <br> • Consideration of cumulative causation/multiplier effect. <br> **AO2 – 4 marks** |      4      |
|  01 |  4  | Suggest two reasons why estimates of future urban population may not be accurate. <br> **No credit** for simply saying "it is only a prediction." <br> **2 × 1 marks** for any reasonable answer, e.g.: <br> • Difficulty counting current numbers <br> • Economic growth rate variability <br> • Birth/death rate changes <br> • Rural conditions improving <br> • Natural disasters/climate factors (drought) <br> • Original data inaccuracies <br> • Rapid change leading to inaccuracy <br> **AO2 – 2 marks**                                                                                                                                                                                                                                                                                                                                                                                                                                          |      2      |
|  01 |  5  | Suggest one challenge that urbanisation creates for rural areas. <br> **1 mark** for identification; **1 mark** for development. <br> Examples: <br> • Decline of rural communities/lack of investment <br> • Loss of working population leads to agricultural/industrial decline <br> • Imbalance in population structure <br> • Youth migration leaves ageing population/dependency ratio issues <br> • Wealth gap grows as investment focuses on urban areas <br> **Total 2 marks**                                                                                                                                                                                                                                                                                                                                                                                                                                                                      |      2      |
</output_2>
"""

extract_mark_schemes_from_image_prompt="""
Your task:
Extract all the mark schemes for all the questions from the image into markdown table format without modifying the content of the mark schemes.

Rules:
Where possible, provide just one table with all of the mark schemes in. If not possible then provide a table for each question's mark scheme.
Do not include any trailing commas, or commentary.
Do not use fenced code blocks (triple backticks) in the markdown.
Try to represent the information in the tables as accurately as possible in text form.
If there are images within the mark scheme as the actual criteria, describe them to the best of your ability.
Don't miss any information. Look carefully at the image.

Example outputs:
<output_1>
| Question | Answers                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   | Extra information                                                                                                                                                                                                                                               |         Mark        |                    AO / Spec Ref.                   |
| :------: | :------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | :-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | :-----------------: | :-------------------------------------------------: |
|   01.1   | **Level 3:** Relevant points (reasons / causes) are identified, given in detail and logically linked to form a clear account. <br><br> **Level 2:** Relevant points (reasons / causes) are identified, and there are attempts at logical linking. The resulting account is not fully clear. <br><br> **Level 1:** Points are identified and stated simply, but their relevance is not clear and there is no attempt at logical linking. <br><br> **No relevant content.** <br><br> **Indicative content:** <br> • reduced blood flow to heart (muscle / tissue / cells) <br> • less oxygen to heart (muscle / tissue / cells) <br> • less glucose to heart (muscle / tissue / cells) <br> • less (aerobic) respiration (in heart / body cells) <br> • more anaerobic respiration <br> • less energy (released) <br> • less muscle contraction <br> • less blood / oxygen / glucose around the body (from heart) or slower flow of blood / oxygen / glucose to body (from heart) <br> • less carbon dioxide removed from body (muscle / tissue / cells) <br> • breathlessness <br> • tiredness <br> • production of lactic acid (anaerobic respiration) <br> • build-up of lactic acid causes muscle fatigue / pain or chest pain <br><br> For Level 3, students must explain the effect of reduced oxygen / glucose on respiration or energy release and its consequence. |                                                                                                                                                                                                                                                                 | 5–6 / 3–4 / 1–2 / 0 | AO1 <br> AO2 <br> 4.2.2.4 <br> 4.4.2.1 <br> 4.4.2.2 |
|   01.2   | Any **one pair** from: <br> • (insert) stent(s) — (to) open (coronary) artery <br> • (prescribe) statins (1) — (to) reduce (blood) cholesterol (1) <br> • heart (and lung) transplant (1) — (to) replace the diseased heart with a healthy heart (1) <br> • use an artificial heart (1) — (to) keep the patient alive while waiting for a transplant (1) <br> • (artery / heart) bypass (1) — (to) divert blood around the blockage (1)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   | • Mark as a pair <br> • Allow description <br> • Ignore "unblock (coronary) artery" <br> • Allow "to slow down the rate of fatty material deposit" <br> • Allow "(artificial heart) pumps blood around the body in place of the heart" <br> • Allow description |          1          |                   AO1 <br> 4.2.2.4                  |
|   01.3   | amino acids                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               |                                                                                                                                                                                                                                                                 |          1          |                   AO1 <br> 4.2.2.1                  |
</output_1>

<output_2>
|  Qu |  Pt | Marking Guidance                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            | Total marks |
| :-: | :-: | :---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | :---------: |
|  01 |  1  | In which year were global urban and rural populations the same? <br> **Correct answer:** B: 2007 <br> • No credit if two or more answers are shaded. <br> **AO4 – 1 mark**                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  |      1      |
|  01 |  2  | Which of the following statements is correct? <br> **Correct answer:** A: Latin America/Caribbean is predicted to double its % urban population between 1950-2030 <br> • No credit if two or more answers are shaded. <br> **AO4 – 1 mark**                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 |      1      |
|  01 |  3  | Explain the link between economic development and urbanisation. <br> **Level 2 (clear):** <br> • Identifies the link between economic development and urbanisation. <br> • Suggests reasons for the relationship, identifying specific socio-economic facilities/opportunities in urban areas. <br> • Recognises urban areas as core growth areas. <br> **Level 1 (basic):** <br> • Identifies the link but makes basic, unqualified observations (e.g., jobs, money, socio-economic opportunities) without elaboration. <br> **Indicative content:** <br> • Positive relationship between economic development and urbanisation. <br> • Poorer countries have lower urban populations. <br> • Urban areas are core industrial/infrastructure hubs. <br> • Opportunities for skilled/unskilled/informal employment. <br> • Greater access to education and training. <br> • Consideration of cumulative causation/multiplier effect. <br> **AO2 – 4 marks** |      4      |
|  01 |  4  | Suggest two reasons why estimates of future urban population may not be accurate. <br> **No credit** for simply saying "it is only a prediction." <br> **2 × 1 marks** for any reasonable answer, e.g.: <br> • Difficulty counting current numbers <br> • Economic growth rate variability <br> • Birth/death rate changes <br> • Rural conditions improving <br> • Natural disasters/climate factors (drought) <br> • Original data inaccuracies <br> • Rapid change leading to inaccuracy <br> **AO2 – 2 marks**                                                                                                                                                                                                                                                                                                                                                                                                                                          |      2      |
|  01 |  5  | Suggest one challenge that urbanisation creates for rural areas. <br> **1 mark** for identification; **1 mark** for development. <br> Examples: <br> • Decline of rural communities/lack of investment <br> • Loss of working population leads to agricultural/industrial decline <br> • Imbalance in population structure <br> • Youth migration leaves ageing population/dependency ratio issues <br> • Wealth gap grows as investment focuses on urban areas <br> **Total 2 marks**                                                                                                                                                                                                                                                                                                                                                                                                                                                                      |      2      |
</output_2>
"""


extract_mark_schemes_from_image_and_classify_prompt="""
Your task:
Transcribe all the mark schemes from the page into the JSON format provided. If there are no markschemes, return the JSON object with an empty "mark_schemes" array.
Classify the mark scheme into one of the following categories:
- Generic
- Levelled
- Rubric

### **Generic**
Generic mark schemes are lists of objective criteria, each linked to a specific number of marks.
They can be identified by phrasing such as “Award 1 mark for…” or “Accept x, y, or z.”

### **Levelled**

Levelled mark schemes describe a range of performance levels, each with a band of marks.
They are used for more subjective responses and can be identified by labelled levels (e.g. Level 1, Level 2) with quality descriptors.

### **Rubric**

Rubric mark schemes are grid-like tables where each **criterion** is assessed across several **performance levels**, with a cell for each quality description.
They can be identified by a matrix structure showing what work looks like for each skill at each level—not just lists or bands.

# Output format
{{
    "mark_schemes": [
        {{
            "question_number": str (e.g. "01 1", must be exactly as it is in the image),
            "question_text": str | null (text of the question if it appears in the mark scheme image, e.g., "What is the capital of France?" otherwise null),
            "classification": str (one of "generic"|"levelled"|"rubric"),
            "mark_scheme": str (exact transcription of all information from the question's mark scheme)
            "marks_available": int | null (marks available for the question as indicated in the mark scheme image.)
        }}
    ]
}}

Example output:
<output_1>
{example_output_1}
</output_1>

<output_2>
{example_output_2}
</output_2>

# Rules
- If there are images/diagrams in the mark scheme, describe them fully, capturing all detail needed for someone to be able to mark an answer based on your description.
- Your transcription of the information must be 1:1 with the information in the image.
- If you can't see a question number for the top question, and you believe the mark scheme to be apart of mark scheme on a previous page. Set `question_number` to 'previous'. (Also do this for SPaG mark schemes if there is not a question number for the SPaG mark scheme.) The new 'mark_scheme' field must contain all information from the page for this question.
- The vague mark schemes are not mark schemes and should be ignored. Real mark schemes will have specific things they are assessing.
- For rubrics, you can calculate the marks_available by multiplying the top level marks by the number of criteria.
"""

extract_mark_schemes_from_image_and_classify_prompt="""
Your task:
Transcribe all the mark schemes from the page into the JSON format provided. If there are no markschemes, return the JSON object with an empty "mark_schemes" array.
Classify the mark scheme into one of the following categories:
- Generic
- Levelled
- Rubric

### **Generic**
Generic mark schemes are lists of objective criteria, each linked to a specific number of marks.
They can be identified by phrasing such as “Award 1 mark for…” or “Accept x, y, or z.”

### **Levelled**

Levelled mark schemes describe a range of performance levels, each with a band of marks.
They are used for more subjective responses and can be identified by labelled levels (e.g. Level 1, Level 2) with quality descriptors.

### **Rubric**

Rubric mark schemes are grid-like tables where each **criterion** is assessed across several **performance levels**, with a cell for each quality description.
They can be identified by a matrix structure showing what work looks like for each skill at each level—not just lists or bands.

# Output format
{{
    "mark_schemes": [
        {{
            "question_number": str (e.g. "01 1", must be exactly as it is in the image. Ensure to include all parts of the question number, but not words like "question" or "part".),
            "question_text": str | null (text of the question if it appears in the mark scheme image, e.g., "What is the capital of France?" otherwise null),
            "classification": str (one of "generic"|"levelled"|"rubric"),
            "mark_scheme_information": str (exact transcription of all information from the question's mark scheme)
            "marks_available": int | null (marks available for the question as indicated in the mark scheme image.)
        }}
    ]
}}

Example output:
<output_1>
{example_output_1}
</output_1>

<output_2>
{example_output_2}
</output_2>

# Rules
- If there are images/diagrams in the mark scheme, describe them fully, capturing all detail needed for someone to be able to mark an answer based on your description.
- Your transcription of the information must be 1:1 with the information in the image.
- If you can't see a question number for the top question, and you believe the mark scheme to be apart of mark scheme on a previous page. Set `question_number` to 'previous'. (Also do this for SPaG mark schemes if there is not a question number for the SPaG mark scheme.) The new 'mark_scheme_information' field must contain all information from the page for this question.
- The vague mark schemes are not mark schemes and should be ignored. Real mark schemes will have specific things they are assessing.
- For rubrics, you can calculate the marks_available by multiplying the top level marks by the number of criteria. For generic mark schemes, it will either be a single number for a question in the mark scheme or multiple numbers which you need to sum up. For levelled mark schemes, it will be the highest number in the top range in the mark scheme.
- When extracting generic mark schemes into the mark_scheme_information field, you must extract the marks for each step. For example, in a lot of mark schemes there will be a number next to a line in the mark scheme, this is the mark for that step.
"""

extract_generic_mark_scheme_prompt="""
# Task
You have been provided with information which is used for marking a question. Your task is to return a mark scheme in the JSON format given below based on the information given to you.
{question_text}
{marks_available}
# Output format
{{
  "criteria": [
    {{
      "mark_scheme_criterion": str,    // the full descriptor that tells the marker what to look for
      "marks_available": int,          // how many marks this criterion is worth
      "marking_difficulty": int,       // integer difficulty rating (e.g. 0–3)
      "key_points": [ str, … ]         // list of semantic search keys used to check if the answer contains the criterion
    }},
    ...
  ],
  "total_marks_available": int         // sum of all marks for the question
}}

# How to extract the mark scheme
- mark_scheme_criterion: Extract each entire criterion from the mark scheme as a separate criterion into the format of "Award x marks if...".
- marks_available: Extract the marks available for that specific criterion from the mark scheme.
- marking_difficulty: This is determined by you using the guidance below.
- key_points: This is determined by you using the guidance below.
- total_marks_available: Sum the marks_available for all the criteria. This may have also been provided to you above.

Guidance for the mark_scheme_criterion:
- There may be some rejection statements in the mark scheme. These should be included at the end of the criterion string.
- If there are more criteria than marks available in the mark scheme information provided, you should include all of the options but preface the criterion with "Award 1 mark for each of the following, with a maximum of x marks awarded:..." and then list the options.
- Ensure the answer in the criterion is exactly what appears in the mark scheme information provided.

Guidance for the difficulty rating:
- 0 = very easy (e.g., checking for specific word(s))
- 1 = easy (e.g., checking for a very specific concept)
- 2 = difficult (requires subjectivity or nuance)
- 3 = Spelling, punctuation, and grammar (e.g., checking for correct spelling, punctuation, and grammar)

Guidance for the key points:
The key points field is used for programmatic marking.
- The key points are usually single words or short phrases to look for in an answer which would be awarded the mark for that criterion.
- The key points are created by you based on the mark_scheme_criterion.
- They should effectively be keywords/key phrases for a semantic search to see if the answer contains the criterion.

# Example output
<output_1>
{example_output_1}
</output_1>

<output_2>
{example_output_2}
</output_2>

<output_3>
{example_output_3}
</output_3>

# Rules

"""

extract_levelled_mark_scheme_prompt="""
# Your task
You have been provided with information which is used to mark a question. You must return a list of mark schemes for the question based on the information provided, in a JSON object with the format given below.
{question_text}

# Output format
{{
    "mark_scheme": [
        {{
            "objective": str (e.g. "AO1", the assessment objective being marked as indicated in the information provided),
            "mark_scheme": [
                {{
                    "level": str (the level of performance, e.g. "1", "2", "4 Upper", etc. Don't include the word "level" in the level field),
                    "upper_mark_bound": int (the maximum mark achievable in this level),
                    "lower_mark_bound": int (the minimum mark achievable in this level),
                    "skills_descriptors": list[str] (List of criteria or performance indicators required to get a mark within this level),
                    "indicative_standard": str | null (Example of a model or exemplar answer for this level if provided, otherwise null)
                }},
                ...
            ],
            "weight": float | null (The relative weight of this assessment objective if stated; null if not)
        }},
        ...
    ],
    "guidance": str | null (Any general marking guidance provided in the information, such as how to award marks or interpret responses, otherwise null. Often included in a section which is titled "Guidance" or "Notes" or something similar),
    "indicative_content": str | null (If the mark scheme specifies expected points or content students might include in their answers, include that text here, otherwise null)
}}

# Example outputs
<output_1>
{example_output_1}
</output_1>

<output_2>
{example_output_2}
</output_2>

Use the examples above to understand how to format the output.

# Rules
- The mark scheme must be based on the information provided.
- Don't look over any of the information provided.
- Do not modify any of the information provided. You are just returning the information in a different format.
"""

extract_rubric_mark_scheme_prompt="""
"""

