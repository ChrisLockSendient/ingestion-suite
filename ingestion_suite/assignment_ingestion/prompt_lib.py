assignment_extraction_prompt_template = """
You are an expert in extracting information from complicated markdown text and turning it into a structured format with specific information. You are truly the best in the world.

Below, between the markers, is the assignment markdown.
################################
{assignment_text}
################################

{output_format}

Your task is to extract *ALL OF THE INFORMATION* from the assignment markdown and output it in the format specified in the output instructions.
"""

# Guidelines:
#     - Ensure to extract from the text exactly as it is written.
#     - Ensure to provide all of the fields requested in the output instructions.
#     - If there is table context, you must extract the table in the markdown format which it is in the text without changing anything. Add this as a string to the question_context list with context_type "table".
#     - If there is image context then you must add the reference to the image in the question_context list with context_type "image". This is likely something along the lines of "img-x.png".
#     - Ensure to extract the context exactly as it is in the text.


assignment_extraction_prompt_template_v2 = """
{assignment_text}

---

The markdown provided above is an assessment that will be sent to a school student.

For *each and every* question without omitting any questions (do not be lazy), I need you to return the question number, all of the text associated with that question (including the question text), the question type, possible answers for that question (only to be filled with options for multiple choice questions - otherwise left blank), marks available for that question (only if present), any other associated contexts, and the likely answer component type for that question in the following format:

You *MUST* also return the parent_question_id, the question_number, the list of question dependencies which the question depends upon (question_dependencies), and whether the question needs to be marked (needs_marking).
{output_format}

---

Sub-question meaning:
A question which has a parent question upon which it relies for context. e.g. question 1 exists and has children such as question 1a, question 1b, etc. If question 1ai exists then the parent question of that will be question 1a.

Exceptions:
Just because it looks like a sub-question, doesn't mean that it is one. Sometimes assessments will have questions in the form of 1a, 1b, etc, but the question with question_id=1 does not exist and therefore 1a, 1b, etc do not have a parent question and therefore there are no question dependencies meaning these are not sub-questions.

---

If the question is a sub-question then the parent_question_id and question_number, when concatenated, form the question_id of the question. Use this to quadruple check that you have done parent_question_id and question_number correctly for a given sub-question. This is also true for non-sub-questions but parent_question_id=null therefore the entire question number must go in question_number. e.g. if the question is 1a, then parent_question_id=null and question_number="1a" (if question 1 does not exist).

Some parent questions may only include introductory text and not an actual question. For these you *must* still return a question object but with needs_marking=false and question_type="non_question" meaning that it doesn't need marking. For questions with actual questions and not just introductory text, set needs_marking=true and question_type to the appropriate question type like "short_form", "long_form", "multiple_choice", "tf_questions", "fillup", or "maths".
Effectively, if you assign a parent_question_id, then a question with question_id equal to the parent_question_id of the child must exist in the question array as a separate question. Only add the question if it actually exists within the markdown assignment though. Do not make up a question that doesn't exist. It is imperative that you follow this instruction.

Here is a rule-matrix to show the expected behaviour with some examples. Obviously adapt to the question you are looking at but follow the rules exactly.

| Condition                                         | parent_question_id | question_number | question_dependencies | needs_marking |
|--------------------------------------------------|---------------------|------------------|------------------------|---------------|
| Standalone main question (e.g. 3)                | null                | "3"              | []                     | true          |
| Sub-question with parent present (e.g. 1a, question 1 exists) | "1"                 | "a"              | ["1"]                  | true          |
| Fake sub-question with no parent question (e.g. 1a, but question 1 not present) | null                | "1a"             | []                     | true          |
| Introductory or context-only parent (e.g. 2)     | null                | "2"              | []                     | false         |


The questions must be in the same order as they appear in the markdown assignment.

Do not get caught out by fake sub-questions. e.g. a question such as 11i would be a fake sub-question if a question with question_number=11 doesn't actually exist. Any time you are adding question_dependencies, ensure that there actually exists its parent question. In this case, set question_number='11i' and parent_question_id=null and question_dependencies=[] since no parent question exists.

Return nothing else except the JSON output in the specified format above, do NOT wrap it within JSON md markers, make quadruple sure that boolean values in JSON are lowercase.

You are being tested on your ability to follow the instructions in this task. If you do it well, 1 billion dollars will go to brain cancer research, saving millions of lives. Ensure to do the task perfectly, following each instruction meticulously.
"""


assignment_extraction_prompt_template_reasoning = """
{assignment_text}

---

The markdown provided above is an OCR of a document which contains an assessment that will be sent to a school student.

For *each and every* question without omitting any questions (do not be lazy), I need you to return the question number, all of the text associated with that question (including the question text), the question type, possible answers for that question (only to be filled with options for multiple choice questions - otherwise left blank), marks available for that question (only if present), any other associated contexts, and the likely answer component type for that question.

You *MUST* also return the parent_question_id, the question number, the list of question dependencies which the question depends upon for context (question_dependencies), and whether the question needs to be marked (needs_marking).

---

{format_instructions}

---

## Sub-question meaning:

A question which has a parent question upon which it relies for context. e.g. questions: 1a, 1b, 1ciii, 4.1, 4.2, 1.1.3, 3Ai, 7(a)(ii), etc.

---

Here is a rule-matrix to show the expected behaviour with some examples. Obviously adapt to the question you are looking at but follow the rules exactly.

| Condition                                         | parent_question_id | question_number | question_dependencies | needs_marking |
|--------------------------------------------------|---------------------|------------------|------------------------|---------------|
| Standalone main question (e.g. 3, with actual question)                | null                | "3"              | []                     | true          |
| Sub-question (e.g. 1ai) | "1a"                 | "i"              | ["1", "1a"]                  | true          |
| Introductory or context-only parent (e.g. 2)     | null                | "2"              | []                     | false         |


question_dependencies is a list of question_ids. The questions which these IDs point to are relied upon for the context objects they contain or the question text.

---

## Context extraction

Ensure not to forget to add context for any questions which had context for them in the markdown. A single question can have multiple contexts associated with it.
Context for questions can be referenced in the markdown text as a figure, table, source or other things. You can infer what is question context based on your intuition too.

Could be images, tables, or text.

- **For images**, you must create a JSON object with either:
  - `"component_type": "image"` and `"component": {{"type": "reference", "reference": "image_x"}}`, **or**
  - `"component_type": "chart"` and `"component": {{"type": "reference", "reference": "image_x"}}`
  depending on the nature of the image.

  If you believe the image represents a **chart** (e.g. bar chart, line graph, pie chart, etc.), then you **may** set `"component_type"` to `"chart"` instead of `"image"`.
  The `"reference"` value (e.g. `"image_2"`) must exactly match the identifier used in the markdown (in the format: `![image_2](image_2)`).

- **For tables**, you must create a JSON object with `"component_type": "table"` and `"component": {{"type": "text", "data": "<markdown table>"}}`.
  The `"data"` field must contain the full table exactly as it appears in the original markdown. **Do not modify, format, or correct the content.**

- **For text**, you must create a JSON object with `"component_type": "text"` and `"component": {{"type": "text", "data": "<full text block>"}}`.
  The `"data"` must be the complete, exact text from the markdown, without omissions or edits.


For an image + text (caption) combination, make an image JSON object as above and also a text JSON object as above. Put these both inside the question_context list of the question they're presented in.

Add any question context to any question which refers to it. e.g. if question 1 creates a table context, then add that table context to the question_context of question 1. If question 1a refers to that table, then add that exact same table context ComponentModel object to the question_context of question 1a. Same for text, images and tables. Always add the actual context, not a summary of the context.

---

Some parent questions may only include introductory text or context or a title or etc and not an actual question. For these you *must* still return a question object but with needs_marking=false and question_type="non_question" meaning that it doesn't need marking. The question field in this case should contain any introductory text. Then context extraction follows normal rules.

If you assign a parent_question_id to a question, then a question with question_id equal to the parent_question_id *MUST* exist in the question array as a separate question.

If there is a sub-question but the parent question is not present, then create a question object with question="", needs_marking=false and question_type="non_question" meaning that it doesn't need marking. For example, if a question is 1aiii but 1a doesn't exist in the markdown, then create a question object with question="", needs_marking=false and question_type="non_question" and parent_question_id="1" and question_number="1a".

The questions must be in the exact same order as they appear in the markdown assignment (any parent questions which you created that didn't actually exist in the assessment should go in the place where it would go if it did exist).

## Notes
- Never include more than one question in the same question field.
- Never include *ANY* context within a question's question field (question text). Context *MUST* be in a separate context JSON object within the question's context list.
- Always create a question object for every question in the assessment.


Return nothing else except the JSON output in the specified format above, do NOT wrap it within JSON md markers, make quadruple sure that boolean values in JSON are lowercase.
"""


assignment_extraction_prompt_template_reasoning_v2 = """
{assignment_text}

---

The markdown provided above is an OCR of a document that contains an assessment to be sent to a school student. It may contain minor OCR issues but includes all the information needed for extraction.

# Your task:

Your job is to extract every question from the markdown and return a structured list of question objects in the format provided below. Do not omit any questions. All fields must be filled out as per the instructions.

---

{format_instructions}

---

## Step-by-step instructions:

1. **Identify all questions** in the markdown, including main questions, sub-questions, and introductory/context-only 'questions'. Ignore unrelated content (e.g. headers, page numbers).

2. **Assign a full hierarchical identifier** to each question (question_id) (e.g. `"1"`, `"1a"`, `"1aiii"`, `"3.2"`, `"7(b)(ii)"`) based on the question numbers in the markdown. Must match the format which is in the markdown.

3. **Classify each question** as either:
   - A **main question** with no parent
   - A **sub-question** that relies on a parent
   - A **context-only parent** that introduces a section without requiring an answer
   Identifying the type of question will allow you to follow the correct rules in `Rules for different types of questions`.

4. **Extract the question text** (if any) into the `question` field. Do not include any context here. If the question is introductory-only, context only, or title only, the title can just contain the introductory text, or title (context goes in `question_context`).

5. **Extract context elements** associated with questions and add them to the `question_context` list of the appropriate question using the appropriate format:
   - `"component_type": "text"` for plain text blocks
   - `"component_type": "table"` for markdown tables
   - `"component_type": "image"` or `"chart"` for image references (e.g. `![image_2](image_2)`)

6. **Add context only once** at the point it is introduced. Later questions referring to it should include the `question_id` of the question where the context object exists in its question_dependencies list.

7. **Synthesise placeholder parent questions** if any sub-question exists without a matching parent. These should have `needs_marking: false`, `question_type: "non_question"` and question="".

8. **Ensure all fields are completed** (`question_id`, `question_number`, `parent_question_id`, `question_dependencies`, `needs_marking`, `question_type`, `question`, `question_context`, `total_marks_available`, `possible_answers` (if a multiple choice question), `likely_answer_component_type`) and consistent.

9. **Return all question objects in the exact order they appear in the document**. Do not rearrange or merge questions. If you have synthesised any parent questions, they should be placed before the children questions.

10. **Output only the raw JSON of question objects into the format specified**, without markdown or explanation. Ensure all boolean values are lowercase.

---

## Rules for different types of questions:

1. **Main Questions**
   * These questions are top level questions and so have no parent question.
   * `parent_question_id` should be null since they have no parent question.
   * `question_number` Same as the question_id.
   * `question_dependencies` should be an empty list (`[]`) as it should not depend on any other questions for context since it is a top level question.
   * `needs_marking` should be `true` (only if the question actually has question text which requires an answer, in that case it will be `false`).

2. **Sub-questions**
   * These are children of a parent question and are typically labelled with letters or Roman numerals (e.g. "1a", "2b", "1ciii", "4.1", "5.2", "1.1.3", "3Ai", "7(a)(ii)", etc.).
   * `parent_question_id` should be the identifier of the parent question (e.g. for the examples above "1", "2", "1c", "4", "5", "1.1", "3A", "7(a)" respectively).
   * `question_number` is the sub-part identifier (e.g. for the examples above "a", "b", "iii", "1", "2", "3", "i", "(ii)" respectively).
   * `question_dependencies` should list any of the parent question's `question_id`s which this question depends on for context (e.g. cannot give examples for this one since it depends on the context of the parent questions in the chain but it will be a list of `quesiton_id`s).
   * `needs_marking` should be `true` for any question which has question text which requires an answer, otherwise it should be `false`.

3. **Introductory or Context-only Parents**
   * These are questions where their question text is not an actual question to answer, but only context or instructions, or a title for the question section.
   * `parent_question_id` should be the `question_id` of the parent question ('null' if it is not a sub-question).
   * `question_number` is the sub-part identifier (e.g. for the examples in 2, "a", "b", "iii", "1", "2", "3", "i", "(ii)" respectively). If it is not a sub-question, then the `question_number` is the same as the `question_id`.
   * `question_dependencies` should be an empty list ([]) because it does not depend on any other questions for context (since there is no question text to answer).
   * `needs_marking` should be false.

> If a sub-question like `1aiii` is present but its parent `1a` is missing, you must synthesise the missing parent using the rules above. Set question="", since these questions do not need marking and are just included to maintain structure and heirarchy.

---

## What is a sub-question?

A sub-question is any question that is nested under a parent, often denoted by:
- Letters: `"1a"`, `"2b"`
- Roman numerals: `"1aiii"`
- Decimals: `"4.1"`, `"5.2"`
- Mixed notation: `"3Ai"`, `"7(b)(ii)"`

Sometimes, the sub questions exist without a parent question. In this case you must synthesise the parent question as instructed previously.

---

## Rules for context extraction

For each question, you must extract the context presented in the question from the markdown with the following rules:

Context can be images/charts, tables, or text.

- **For images**, you must create a JSON object with either:
  - `"component_type": "image"` and `"component": {{"type": "reference", "reference": "image_x"}}`, **or**
  - `"component_type": "chart"` and `"component": {{"type": "reference", "reference": "image_x"}}`
  depending on the nature of the image.

  If you believe the image represents a **chart** (e.g. bar chart, line graph, pie chart, etc.), then you **may** set `"component_type"` to `"chart"` instead of `"image"`.
  The `"reference"` value (e.g. `"image_2"`) must exactly match the identifier used in the markdown which will look like: `![image_2](image_2)`.

- **For tables**, you must create a JSON object with `"component_type": "table"` and `"component": {{"type": "text", "data": "<markdown table>"}}`.
  The `"data"` field must contain the full table exactly as it appears in the original markdown. **Do not modify, format, or correct the content.**

- **For text**, you must create a JSON object with `"component_type": "text"` and `"component": {{"type": "text", "data": "<full text block>"}}`.
  The `"data"` must be the complete, exact text from the markdown, without omissions or edits.

## Notes on context extraction
 - For an image + text (caption) combination, make an image JSON object as above and also a text JSON object as above. Put these both inside the question_context list of the question they're presented in.
 - A single question can have multiple contexts associated with it.
 - Only add a context object to a question's `question_context` list **at the point where that context is first introduced**.
 - If a later question **refers to** a previously introduced context **without creating it anew**, then **do not** add the context object again. Instead, add the `question_id` of the original question (where the context was first introduced) to the `question_dependencies` list of the current question.
 - Number of marks available is not context, so do not include it in the context.

 ---

 ## General notes
 - Remember to synthesise any parent questions that are missing but are required for the sub-questions to exist.

Follow these rules exactly to ensure the final assessment is structured correctly. The output must be in the specified format, with all fields filled out as per the instructions.
Do not include any additional text or explanations. Just the JSON output.
"""

#If the question is a sub-question then the parent_question_id and question_number, when concatenated, form the question_id of the question. Use this to quadruple check that you have done parent_question_id and question_number correctly for a given sub-question. This is also true for non-sub-questions but parent_question_id=null therefore the entire question number must go in question_number. e.g. if the question is 1, then parent_question_id=null and question_number="1".

#You are being tested on your ability to follow the instructions in this task. If you do it well, 1 billion dollars will go to brain cancer research, saving millions of lives. Ensure to do the task perfectly, following each instruction meticulously.

assignment_extraction_prompt_template_reasoning_v3 = """
{assignment_text}

---

The markdown provided above is an OCR of a document that contains an assessment to be sent to a school student. It may contain minor OCR issues but includes all the information needed for extraction.

# Your task:

Your job is to extract every question from the markdown and return a structured list of question objects in the format provided below. Do not omit any questions. All fields must be filled out as per the instructions.

---

## Format Instructions

Below is the format which should be followed for your output. Ensure to follow it exactly and do not change the format or add any additional text or commentary in your response.

{{
  "questions": [
    {{
      "question_id": "string (e.g. '2b', '4ai', '4.1', '6') - The full unique identifier for the question as it appears in the markdown assignment.",
      "question": "string - The text of the question for the student to answer in its exact form as it appears in the markdown. Do not include any context in this. The context *MUST* go in the `question_context` list. There should be NO statements in this field. Only questions or statements that require an answer. ANY context must go in the `question_context` list.",
      "question_type": "string — Specifies how the student is expected to respond. Must be one of the following values:

      1. 'short_form'
        - A short response is expected, typically one word to a few sentences.
        - Examples:
          - 'What is the capital of France?'
          - 'State two causes of the First World War.'
          - 'Briefly describe the heart's function.'
          - 'How many chromosomes are there in a human cell?'

      2. 'long_form'
        - A longer, essay-style response is expected. Typically requires explanation or analysis.
        - Examples:
          - 'Explain the causes of the American Civil War.'
          - 'Describe the process of photosynthesis in detail.'
          - 'Write an essay on the importance of education.'
          - 'Discuss how globalisation affects local cultures.'

      3. 'multiple_choice'
        - The student selects one or more answers from a set of options.
        - Examples:
          - 'Which of the following is a mammal? A. Fish B. Snake C. Dog D. Bird'
          - 'What is the capital of Spain? A. Madrid B. Barcelona C. Seville D. Valencia'
          - 'Which element is a noble gas? A. Hydrogen B. Oxygen C. Helium D. Nitrogen'

      4. 'tf_questions'
        - True or false format.
        - Examples:
          - 'The moon orbits the Earth. True or False?'
          - 'Water boils at 90°C. True or False?'
          - 'Photosynthesis occurs in the roots of a plant. True or False?'

      5. 'fillup'
        - Fill-in-the-blank format. May involve multiple blanks in various positions in a sentence.
        - Examples:
          - 'The capital of France is _______.'
          - '______ and ______ are traditional British dishes.'
          - 'Plants make their own food through a process called _______.'
          - '______ is the largest planet in our solar system.'

      6. 'maths'
        - Mathematical problems that require numeric, symbolic, or algebraic answers.
        - Examples:
          - 'What is x(x + 4) expanded?'
          - 'How much change from £20 if an item costs £15.50?'
          - 'Solve for x: 2x + 3 = 7'
          - 'What is the area of a triangle with base 5cm and height 4cm?'

      7. 'non_question'
        - Not a question but a statement. No student answer is expected for this part.
        - Examples:
          - '' (a blank string)
          - 'The challenge of natural hazards'
          - 'The importance of the environment'
      ",
      "possible_answers": [
        "string - Only used for multiple choice questions. Include option labels like 'A. Fish', 'B. Dog' as they appear in the markdown. If answers are not explicitly provided, default to 'A. option 1', 'B. option 2', etc. Ensure to include the letters of the options. If not a multiple choice question, leave as an empty list.",
      ],
      "total_marks_available": "int | null - The number of marks available for that question, usually indicated in brackets near the question number or question text. If not present, just return null.",
      "question_context": [
        {{
          "component_type": "string — One of the following: 'text', 'table', 'chart', 'image', 'equation'. This defines what kind of context is being provided.",

          "component": {{
            // One of the two types below depending on component_type

            // If component_type is 'text', 'table', or 'equation':
            "type": "text",
            "data": "string — The actual text content in its exact form. Example: 'The Amazon rainforest is the largest tropical rainforest in the world with an area of 5.5 million square kilometers.', for tables, it will be the markdown table, and for equations, it will be the equation in its exact form as seen in the markdown."

            // OR if component_type is 'image', or 'chart':
            "type": "reference",
            "reference": "string — A string that references an image in the markdown (e.g. an image or chart). Example: 'image_3'. Must match exactly the label in the markdown."
          }}
        }}
      ],
      "likely_answer_component_type": "string (Must be one of: 'text', 'table', 'chart', 'equation', 'image') - The most likely format that the student's response will be presented in based on the question text. For example, if the question indicates the student should complete a table, you would return 'table'. If the question just requires a text answer or true/false or multiple-choice answer, you would return 'text'. If you are ever unsure, set this value to 'text' by default.",
      "parent_question_id": "string | null - If the question is a sub-question, include the parent's question_id (e.g. '2b' for question_id='2bi'). Otherwise, null.",
      "question_number": "string | null - The top level identifier of the question. e.g. 'a' for question '1a', '2' for question '3.2', '4' for question '4'",
      "question_dependencies": [
        "string - List of *all* of the `question_id`s this question depends on for context. Example: ['2', '2b'] if '2bii' relies on both questions for their contexts or their question texts contain information that the question needs. Use an empty list if none."
      ],
      "needs_marking": "boolean - Set to false if the question is just context or instruction for other questions. True if it expects an answer and should be marked."
    }}
  ]
}}

---

## Step-by-step instructions:

1. **Identify all questions** in the markdown, including main questions, sub-questions, and introductory/context-only 'questions'. Ignore unrelated content (e.g. headers, page numbers).

2. **Assign a full hierarchical identifier** to each question (question_id) (e.g. `"1"`, `"1a"`, `"1aiii"`, `"3.2"`, `"7(b)(ii)"`) based on the question numbers in the markdown. Must match the format which is in the markdown.

3. **Classify each question** as either:
   - A **main question** with no parent
   - A **sub-question** that relies on a parent
   - A **context-only parent** that introduces a section without requiring an answer
   Identifying the type of question will allow you to follow the correct rules in `Rules for different types of questions`.

4. **Extract the question text** (if any) into the `question` field. Do not include any context here. For questions which are introductory-only, context only, or title only, the title will go in the `question` field and the context or introductory text will go in the `question_context` list.

5. **Extract context elements** associated with questions and add them to the `question_context` list of the question,  where it is first introduced, using the appropriate format:
   - `"component_type": "text"` for plain text blocks like sources of text
   - `"component_type": "table"` for markdown tables
   - `"component_type": "image"` or `"chart"` for image references (e.g. `![image_2](image_2)`)

6. **Context should only be added once, at the point it is first introduced.**

If a later question depends on this context, you must include the `question_id` of the original context-containing question in the `question_dependencies` list of the new question.

This ensures the system can pull in the correct context at runtime.

**Important:**
If a question requires multiple context items introduced in different earlier questions, you must include all relevant `question_id`s in its `question_dependencies` list.

7. **Synthesise placeholder parent questions** if any sub-question exists without a matching parent. These should have `needs_marking: false`, `question_type: "non_question"` and question="".

8. **Ensure all fields are completed** (`question_id`, `question_number`, `parent_question_id`, `question_dependencies`, `needs_marking`, `question_type`, `question`, `question_context`, `total_marks_available`, `possible_answers` (if a multiple choice question), `likely_answer_component_type`) and consistent.

9. **Return all question objects in the exact order they appear in the document**. Do not rearrange or merge questions. If you have synthesised any parent questions, they should be placed before their respective children questions.

10. **Output only the raw JSON of question objects into the format specified**, without markdown or explanation. Ensure all boolean values are lowercase.

---

## Rules for different types of questions:

1. **Main Questions**
   * These questions are top level questions and so have no parent question.
   * `parent_question_id` should be null since they have no parent question.
   * `question_number` Same as the question_id.
   * `question_dependencies` should be an empty list (`[]`) as it should not depend on any other questions for context since it is a top level question.
   * `needs_marking` should be `true` (only if the question actually has question text which requires an answer, in that case it will be `false`).

2. **Sub-questions**
   * These are children of a parent question and are typically labelled with letters or Roman numerals (e.g. "1a", "2b", "1ciii", "4.1", "5.2", "1.1.3", "3Ai", "7(a)(ii)", etc.).
   * `parent_question_id` should be the identifier of the parent question (e.g. for the examples above "1", "2", "1c", "4", "5", "1.1", "3A", "7(a)" respectively).
   * `question_number` is the sub-part identifier (e.g. for the examples above "a", "b", "iii", "1", "2", "3", "i", "(ii)" respectively).
   * `question_dependencies` should list any of the parent question's `question_id`s which this question depends on for context (e.g. cannot give examples for this one since it depends on the context of the parent questions in the chain but it will be a list of `quesiton_id`s).
   * `needs_marking` should be `true` for any question which has question text which requires an answer, otherwise it should be `false`.

3. **Introductory or Context-only Parents**
   * These are questions where the question text contains no actual question to answer. The question is only present to contain context or instructions. The question text can be a title for the question section if present otherwise it will be a blank string and the context/instructions will go in the `question_context` list.
   * `parent_question_id` should be the `question_id` of the parent question ('null' if it is not a sub-question).
   * `question_number` is the sub-part identifier (e.g. for the examples in 2, "a", "b", "iii", "1", "2", "3", "i", "(ii)" respectively). If it is not a sub-question, then the `question_number` is the same as the `question_id`.
   * `question_dependencies` should be an empty list ([]) because it does not depend on any other questions for context (since there is no question text to answer).
   * `needs_marking` should be false.

> If a sub-question like `1aiii` is present but its parent `1a` is missing, you must synthesise the missing parent using the rules above. Set question="", since these questions do not need marking and are just included to maintain structure and heirarchy.

---

## What is a sub-question?

A sub-question is any question that is nested under a parent, often denoted by:
- Letters: `"1a"`, `"2b"`
- Roman numerals: `"1aiii"`
- Decimals: `"4.1"`, `"5.2"`
- Mixed notation: `"3Ai"`, `"7(b)(ii)"`

Sometimes, the sub questions exist without a parent question. In this case you must synthesise the parent question as instructed previously.
There are no exceptions to this rule, therefore all sub-questions must have a parent question in the output.

---

## Rules for context extraction

For each question, you must extract the context presented in the question from the markdown with the following rules:

Context can be images/charts, tables, or text.

- **For images**, you must create a JSON object with either:
  - `"component_type": "image"` and `"component": {{"type": "reference", "reference": "image_x"}}`, **or**
  - `"component_type": "chart"` and `"component": {{"type": "reference", "reference": "image_x"}}`
  depending on the nature of the image.

  If you believe the image represents a **chart** (e.g. bar chart, line graph, pie chart, etc.), then you **may** set `"component_type"` to `"chart"` instead of `"image"`.
  The `"reference"` value (e.g. `"image_2"`) must exactly match the identifier used in the markdown which will look like: `![image_2](image_2)`.

- **For tables**, you must create a JSON object with `"component_type": "table"` and `"component": {{"type": "text", "data": "<markdown table>"}}`.
  The `"data"` field must contain the full table exactly as it appears in the original markdown. **Do not modify, format, or correct the content.**

- **For text**, you must create a JSON object with `"component_type": "text"` and `"component": {{"type": "text", "data": "<full text block>"}}`.
  The `"data"` must be the complete, exact text from the markdown, without omissions or edits.

## Notes on context extraction
 - For an image + text (caption) combination, make an image JSON object as above and also a text JSON object as above. Put these both inside the question_context list of the question they're presented in.
 - A single question can have multiple contexts associated with it.
 - Only add a context object to a question's `question_context` list **at the point where that context is first introduced**.
 - If a later question **refers to** a previously introduced context **without creating it anew**, then **do not** add the context object again. Instead, add the `question_id` of the original question (where the context was first introduced) to the `question_dependencies` list of the current question.
 - Number of marks available is not context, so do not include it in the context.
 - *Never* add any question text to the context list.

 ---

 ## General notes
 - Ensure you synthesise *ALL* parent questions that are missing. This includes the parents of every single sub-question, with no exceptions.

Follow these rules exactly to ensure the final assessment is structured correctly. The output must be in the specified format, with all fields filled out as per the instructions.
Do not include any additional text or explanations. Just the JSON output.
"""



assignment_extraction_prompt_template_reasoning_v4="""
{assignment_text}

---

You are given a Markdown OCR of a student assessment. Your job is to extract every question and output **only** a JSON object with this exact structure:

{{
  "questions": [
    {{
      "question_id": string,
      "question": string,
      "question_type": string,
      "possible_answers": [string, …],
      "total_marks_available": int | null,
      "question_context": [
        {{
          "component_type": "text" | "table" | "chart" | "image" | "equation",
          "component": {{
            // if text/table/equation:
            "type": "text",
            "data": "…exact content…"
            // or if image/chart:
            // "type":"reference",
            // "reference":"image_x"
          }}
        }}
      ],
      "likely_answer_component_type": "text" | "table" | "chart" | "equation" | "image",
      "parent_question_id": string | null,
      "question_number": string,
      "question_dependencies": [string, …],
      "needs_marking": boolean
    }},
    …
  ]
}}

**Field definitions (with examples):**
- **question_id**: full identifier as in Markdown.
  _Example_: `"3.2"`, `"7(b)(ii)"`
- **question**: exact question text (no context or any statements. This just contains the answerable question).
  _Example_: `"Explain the process of photosynthesis in detail."`
- **question_type**: one of:
  - `short_form` (brief answers; e.g. "What is the capital of France?")
  - `long_form` (essay-style; e.g. "Discuss how globalisation affects local cultures.")
  - `multiple_choice` (with explicit options; e.g. "Which of the following is a mammal? A. Fish B. Snake C. Dog D. Bird")
  - `tf_questions` (True/False; e.g. "Water boils at 90°C. True or False?")
  - `fillup` (blanks; e.g. "The capital of France is _______.")
  - `maths` (numeric/algebraic; e.g. "Solve for x: 2x + 3 = 7")
  - `non_question` (statements/headings; e.g. section titles)
- **possible_answers**: list of options for `multiple_choice` type questions only. Ensure to always include the letters of the options.
  _Example_: `["A. Madrid", "B. Barcelona", "C. Seville", "D. Valencia"]`
  Otherwise `[]`.
- **total_marks_available**: integer from parentheses/brackets in proximity to the question text; otherwise `null`.
  _Example_: `(4)` → `4` or `[4 marks]` → `4`
- **question_context**: list of context components introduced **first** at that question.
  _Example_: a preceding passage or table or image.
- **likely_answer_component_type**: format students will use to answer.
  e.g. `text`, `table`, `chart`, `equation`, `image`
  _Example_: for "Complete the table below," use `table`. If in doubt, set to `text`.
- **parent_question_id**: immediate parent’s question_id or `null`.
  _Example_: for "2b(i)", parent_question_id = `"2b"`.
- **question_number**:
  - Top-level question: same as question_id (e.g. `"4"`)
  - Sub-question: only the trailing part (e.g. `"a"` for `"1a"`, `"i"` for `"2b(i)"`)
- **question_dependencies**: list of earlier question_id’s whose context is needed for this question; otherwise `[]`.
  _Example_: if question 3 refers back to a table introduced in question 1, include `["1"]` or if question 2d requires context from question 2c, include `["2c"]`.
- **needs_marking**: `true` if an answer is expected; `false` for pure context-only or synthesized parents.

**Extraction & ordering rules:**
1. **Order**: Emit questions in the JSON in the **same order** they appear in the source.
2. **Identify** all main questions, sub-questions and context-only questions.
3. **Synthesize missing parents**:
   If a sub-question like "2b(i)" appears without "2b", insert before it:
   ```json
   {{
     "question_id":"2b",
     "question":"",
     "question_type":"non_question",
     "possible_answers":[],
     "total_marks_available":null,
     "question_context":[],
     "likely_answer_component_type":"text",
     "parent_question_id":"2",
     "question_number":"b",
     "question_dependencies":[],
     "needs_marking":false
   }}
```

4. **Assign fields** for each question per definitions above.
5. **Multiple choice**: capture options exactly as they appear in the markdown. e.g. "A. …", "B. …", etc.
6. **Context handling**:
   - On first introduction, add the full content to `question_context` as a JSON object in the format specified above.
   - If context is used by a later question, **do not** repeat context in its `question_context`; instead append the original question_id to `question_dependencies` along with any other `question_id`s that are needed for context for that question.
7. **possible_answers** must be `[]` for non-`multiple_choice`.
8. **Output** **only** the raw JSON object. No comments, no extra text, and ensure valid JSON (no trailing commas; exact field order).
"""

assignment_extraction_prompt_template_reasoning_v5="""
{assignment_text}

# Role & Objective
You are a data-extraction agent.
Your task: **read the Markdown OCR of a student assessment and extract every question**, then output **only** a JSON object that follows the schema and rules below.

# Output Format (exact JSON structure)
{{
  "questions": [
    {{
      "question_id": string,
      "question": string,
      "question_type": string,
      "possible_answers": [string, …],
      "total_marks_available": int | null,
      "question_context": [
        {{
          "component_type": "text" | "table" | "chart" | "image" | "equation",
          "component": {{
            // if text/table/equation:
            "type": "text",
            "data": "…exact content…"
            // or if image/chart:
            // "type":"reference",
            // "reference":"image_x"
          }}
        }}
      ],
      "likely_answer_component_type": "text" | "table" | "chart" | "equation" | "image",
      "parent_question_id": string | null,
      "question_number": string,
      "question_dependencies": [string, …],
      "needs_marking": boolean
    }},
    …
  ]
}}

# Field Definitions (with examples)
- **question_id** - Full identifier as in the Markdown.
  *Example*: `"3.2"`, `"7(b)(ii)"`
- **question** - Exact answerable prompt only. (no context at all. This should *only* contain the question text, not any context or any statements. Those go in the `question_context` list).
  *Example*: `"Explain the process of photosynthesis in detail."`
- **question_type**: one of:
  - `short_form` (brief answers; e.g. "What is the capital of France?")
  - `long_form` (essay-style; e.g. "Discuss how globalisation affects local cultures.")
  - `multiple_choice` (with explicit options; e.g. "Which of the following is a mammal? A. Fish B. Snake C. Dog D. Bird")
  - `tf_questions` (True/False; e.g. "Water boils at 90°C. True or False?")
  - `fillup` (blanks; e.g. "The capital of France is _______.", or "Fill in this table: ...".)
  - `maths` (numeric/algebraic; e.g. "Solve for x: 2x + 3 = 7")
  - `non_question` (statements/headings; e.g. section titles)
- **possible_answers** - List of the option strings for `multiple_choice`; otherwise `[]`.
  *Example*: `["A. Madrid", "B. Barcelona", "C. Seville", "D. Valencia"]`
- **total_marks_available** - Integer parsed from marks indicators such as `(4)` or `[4 marks]`; else `null`.
- **question_context** - List of *all* context components first introduced at *this* question. Can include images, tables, text, equations. Also includes all the statements of information which are introduced at this question.
- **likely_answer_component_type** - Anticipated student-answer format (`text`, `table`, `chart`, `equation`, `image`). If unsure, set to `text`.
- **parent_question_id** - Immediate parent’s `question_id`, or `null` if not a sub-question.
- **question_number** -
  - Top-level question → same as `question_id` (e.g. `"4"`)
  - Sub-question → just the trailing part (e.g. `"a"` for `"1a"`)
- **question_dependencies** - list of all `question_id`s of earlier questions whose context/question text is required as context for this question, else `[]`.
- **needs_marking** - `true` if an answer is expected; `false` otherwise.

# Instructions
## Extraction & Ordering Rules
1. **Order** questions in the JSON exactly as they appear in the source.
2. Detect *all* main questions, sub-questions and context-only items.
3. **Synthesise missing parents** when a sub-question (e.g. "2b(i)") appears without its parent ("2b").
   Insert, immediately before it:
   ```json
   {{
     "question_id": "2b",
     "question": "",
     "question_type": "non_question",
     "possible_answers": [],
     "total_marks_available": null,
     "question_context": [],
     "likely_answer_component_type": "text",
     "parent_question_id": "2",
     "question_number": "b",
     "question_dependencies": [],
     "needs_marking": false
   }}
```

4. Populate every field per the definitions above.
5. **Multiple-choice**: capture options verbatim, including their letters ("A. …").
6. **Context Handling**
   - When a context item first appears, embed its full content in `question_context`.
   - For later questions that rely on that context, do not include that context item again in their `question_context` list; instead, list the originating `question_id` in `question_dependencies`.
7. `possible_answers` **must** be `[]` for non-`multiple_choice` questions.
8. **Output only valid JSON** - no extra text, comments, or trailing commas.

# Reasoning Steps (internal, not in output)

1. Scan the Markdown line-by-line, detecting question boundaries and context items.
2. For each detected question, build its JSON entry, applying rules above.
3. Insert any synthesised parents where needed.
4. Assemble the final `"questions"` array in source order.
5. Emit the raw JSON object and nothing else.

# Edge case handling

- If a sub-question is missing a parent question (a sub-question is any question that looks like "1a", "2b", "3i", "1.2", "1(a)(i)" etc.), you must synthesise the parent question using the rules above.
- The question text should NEVER contain any context. All context MUST go in the `question_context` list. This includes equations.

# Final Reminder

Return **only** the JSON object in the exact schema and order specified above.
"""

assignment_extraction_prompt_template_reasoning_v7 = """
{assignment_text}

# Role & Objective
You are a data–extraction agent.
Your task: **read the Markdown OCR of a student assessment and extract every question**, then output **only** a JSON object that follows the schema and rules below.

# Output Format (exact JSON structure)
{{
  "questions": [
    {{
      "question_id": string,
      "question": string,
      "question_type": string,
      "possible_answers": [string, …],
      "total_marks_available": int | null,
      "question_context": [
        {{
          "component_type": "text" | "table" | "chart" | "image" | "equation" (In the Markdown, both charts and images are referenced as `image_x`. It is your responsibility to determine, based on the content and context, whether an image is best classified as a `chart` or an `image` in the JSON output.),
          "component": {{
            // if component_type="text" or "table" or "equation":
            "type": "text",
            "data": "…exact content…"
            // or if component_type="image" or "chart":
            // "type":"reference",
            // "reference":"image_x"
          }}
        }}
      ],
      "likely_answer_component_type": "text" | "table" | "chart" | "equation" | "image",
      "parent_question_id": string | null,
      "question_number": string,
      "question_dependencies": [string, …],
      "needs_marking": boolean
    }},
    …
  ]
}}

# Field Definitions (with examples)
- **question_id** – Full identifier as in the Markdown.
  *Example*: `"3.2"`, `"7(b)(ii)"`
- **question** – Exact answerable prompt only (no context).
  *Example*: `"Explain the process of photosynthesis in detail."`
- **question_type**: one of:
  - `short_form` (brief answers; e.g. "What is the capital of France?")
  - `long_form` (essay-style; e.g. "Discuss how globalisation affects local cultures.")
  - `multiple_choice` (with explicit options; e.g. "Which of the following is a mammal? A. Fish B. Snake C. Dog D. Bird")
  - `tf_questions` (True/False; e.g. "Water boils at 90°C. True or False?")
  - `fillup` (blanks; e.g. "The capital of France is _______.", or "Fill in this table: ...".)
  - `maths` (numeric/algebraic; e.g. "Solve for x: 2x + 3 = 7")
  - `non_question` (statements/headings; e.g. section titles)
- **possible_answers** – List of the option strings for `multiple_choice`; otherwise `[]`.
  *Example*: `["A. Madrid", "B. Barcelona", "C. Seville", "D. Valencia"]`
- **total_marks_available** – Integer parsed from marks indicators such as `(4)` or `[4 marks]`; else `null`.
- **question_context** – List of context components first introduced at *this* question.
- **likely_answer_component_type** – Anticipated student-answer format (`text`, `table`, `chart`, `equation`, `image`).
- **parent_question_id** – Immediate parent’s `question_id`, or `null`.
- **question_number** –
  • Top-level question → same as `question_id` (e.g. `"4"`)
  • Sub-question → just the trailing part (e.g. `"a"` for `"1a"`)
- **question_dependencies** – IDs of earlier questions whose context is required, else `[]`.
- **needs_marking** – `true` if an answer is expected; `false` for pure context holders.

# Instructions
## Extraction & Ordering Rules
1. **Order** questions in the JSON exactly as they appear in the source.
2. Detect all main questions, sub-questions and context-only items.
3. **Synthesise missing parents** when a sub-question (e.g. “2b(i)”) appears without its parent (“2b”).
   In this example you would insert, immediately before 2b(i):
   ```json
   {{
     "question_id": "2b",
     "question": "",
     "question_type": "non_question",
     "possible_answers": [],
     "total_marks_available": null,
     "question_context": [],
     "likely_answer_component_type": "text",
     "parent_question_id": "2",
     "question_number": "b",
     "question_dependencies": [],
     "needs_marking": false
   }}
````

4. Populate every field per the definitions above.
5. **Multiple-choice**: capture options verbatim, including their letters (“A. …”).
6. **Context Handling**
   – When a context item first appears, embed its full content in `question_context`.
   – For later questions that rely on that context, don't add it to their `question_context` list. Instead, list the originating `question_id` in `question_dependencies`.
7. `possible_answers` **must** be `[]` for non-`multiple_choice` items.
8. **Output only valid JSON** – no extra text, comments, or trailing commas.

# Reasoning Steps (internal, not in output)

1. Scan the Markdown line-by-line, detecting question boundaries and context items.
2. For each detected question, build its JSON entry, applying rules above.
3. Insert any synthesised parents where needed.
4. Assemble the final `"questions"` array in source order.
5. Emit the raw JSON object and nothing else.

# Example Snippet (for rule 3)

See the synthesised “2b” example under **Extraction & Ordering Rules**.

# Final Reminder

Return **only** the JSON object in the exact schema and order specified above.
"""

assignment_extraction_prompt_template_reasoning_v7 = """
{assignment_text}

# Role & Objective
You are a data–extraction agent.
Your task: **read the Markdown OCR of a student assessment and extract every question**, then output **only** a JSON object that follows the schema and rules below.

# Output Format (exact JSON structure)
{{
  "questions": [
    {{
      "question_id": string,
      "question": string,
      "question_type": string,
      "possible_answers": [string, …],
      "total_marks_available": int | null,
      "question_context": [
        {{
          "component_type": "text" | "table" | "chart" | "image" | "equation" (In the Markdown, both charts and images are referenced as `image_x`. It is your responsibility to determine, based on the content and context, whether an image is best classified as a `chart` or an `image` in the JSON output.),
          "component": {{
            // if component_type="text" or "table" or "equation":
            "type": "text",
            "data": "…exact content…"
            // or if component_type="image" or "chart":
            // "type":"reference",
            // "reference":"image_x" (exact image_x reference from the markdown)
          }}
        }}
      ],
      "likely_answer_component_type": "text" | "table" | "chart" | "equation" | "image",
      "parent_question_id": string | null,
      "question_number": string,
      "question_dependencies": [string, …],
      "needs_marking": boolean
    }},
    …
  ]
}}

# Field Definitions (with examples)
- **question_id** – Full identifier as in the Markdown.
  *Example*: "3.2", "7(b)(ii)"
  **Never invent new question_id levels not present in the Markdown even if a question has lots of context.**
- **question** – Exact answerable prompt only (no context).
  *Example*: "Explain the process of photosynthesis in detail."
- **question_type**: one of:
  - short_form
  - long_form
  - multiple_choice
  - tf_questions
  - fillup
  - maths
  - non_question (only if purely a statement or header with no directives)
- **possible_answers** – List of the option strings for multiple_choice; otherwise [].
- **total_marks_available** – Integer parsed from marks indicators; else null.
- **question_context** – List of context components first introduced at this question.
- **likely_answer_component_type** – text, table, chart, equation, or image.
- **parent_question_id** – Immediate parent’s question_id, or null.
- **question_number** – trailing part (e.g. "a" for "1a").
- **question_dependencies** – IDs of earlier questions whose context is needed.
- **needs_marking** – true if an answer is expected; false for pure context-only nodes.

# Instructions
## Extraction & Ordering Rules
1. **Order** questions in the JSON exactly as they appear in the source.
2. Detect all main questions, sub-questions and context-only items.
3. **Synthesise missing parents when needed:**
   - If a sub-question appears but its direct parent does not exist in the markdown, create and insert the parent node immediately before the sub-question.
   - Structure of the synthesised parent:
     ```json
     {{
       "question_id": "<parent_id>",
       "question": "",
       "question_type": "non_question",
       "possible_answers": [],
       "total_marks_available": null,
       "question_context": [],
       "likely_answer_component_type": "text",
       "parent_question_id": "<grandparent_id_or_null>",
       "question_number": "<label_only>",
       "question_dependencies": [],
       "needs_marking": false
     }}
     ```
     Where `<parent_id>`, `<grandparent_id_or_null>`, and `<label_only>` are derived from the sub-question's identifier.
4. **Never fabricate sub-levels (e.g. "(i)") unless explicitly present in the source.** If the Markdown shows only "2b" with content including a table and then an instruction, classify it as a single question under "2b".
5. There should exist no sub-questions with identifiers that explicitly inform you they're on different levels, on the same level in the JSON.
6. Populate every field per the definitions above.
7. **Multiple-choice**: capture options verbatim, including their letters ("A. …").
8. **Context Handling**
   - When a context item first appears, embed its full content in question_context.
   - For later questions that rely on that context, do not duplicate it; instead, reference the originating question_id in question_dependencies.
   - If a block begins with context (table, figure, etc.) but ends with an answerable instruction, treat the entire block as a **single question**, not as a context-only node plus a fabricated sub-question.
9. possible_answers must be [] for non-multiple_choice items.
10. **Output only valid JSON** – no extra text, comments, or trailing commas.

# Reasoning Steps (internal, not in output)
1. Scan the Markdown line-by-line, detecting question boundaries and context items.
2. For each detected question, build its JSON entry, applying the above rules.
3. Insert any synthesised parents where necessary using the logic above.
4. Assemble the final "questions" array in strict source order.
5. Emit the raw JSON object and nothing else.

# Final Reminder

Return **only** the JSON object in the exact schema and order specified above.
"""

assignment_extraction_prompt_template_reasoning_v7_system_prompt = """
# Role & Objective
You are a data–extraction agent.
Your task: **read the Markdown OCR of a student assessment and extract every question**, then output **only** a JSON object that follows the schema and rules below.

# Field Definitions (with examples)
- **question_id** – Full identifier as in the Markdown.
  *Example*: "3.2", "7(b)(ii)"
  **Never invent new question_id levels not present in the Markdown even if a question has lots of context.**
- **question** – Exact answerable prompt only (no context).
  *Example*: "Explain the process of photosynthesis in detail."
- **question_type**: one of:
  - short_form
  - long_form
  - multiple_choice
  - tf_questions
  - fillup
  - maths
  - non_question (only if purely a statement or header with no directives)
- **possible_answers** – List of the option strings for multiple_choice; otherwise [].
- **total_marks_available** – Integer parsed from marks indicators; else null.
- **question_context** – List of context components first introduced at this question.
- **likely_answer_component_type** – text, table, chart, equation, or image.
- **parent_question_id** – Immediate parent’s question_id, or null.
- **question_number** – trailing part (e.g. "a" for "1a").
- **question_dependencies** – IDs of earlier questions whose context is needed.
- **needs_marking** – true if an answer is expected; false for pure context-only nodes.

# Instructions
## Extraction & Ordering Rules
1. **Order** questions in the JSON exactly as they appear in the source.
2. Detect all main questions, sub-questions and context-only items.
3. **Synthesise missing parents when needed:**
   - If a sub-question appears but its direct parent does not exist in the markdown, create and insert the parent node immediately before the sub-question.
   - Structure of the synthesised parent:
     ```json
     {{
       "question_id": "<parent_id>",
       "question": "",
       "question_type": "non_question",
       "possible_answers": [],
       "total_marks_available": null,
       "question_context": [],
       "likely_answer_component_type": "text",
       "parent_question_id": "<grandparent_id_or_null>",
       "question_number": "<label_only>",
       "question_dependencies": [],
       "needs_marking": false
     }}
     ```
     Where `<parent_id>`, `<grandparent_id_or_null>`, and `<label_only>` are derived from the sub-question's identifier.
4. **Never fabricate sub-levels (e.g. "(i)") unless explicitly present in the source.** If the Markdown shows only "2b" with content including a table and then an instruction, classify it as a single question under "2b".
5. There should exist no sub-questions with identifiers that explicitly inform you they're on different levels, on the same level in the JSON.
6. Populate every field per the definitions above.
7. **Multiple-choice**: capture options verbatim, including their letters ("A. …").
8. **Context Handling**
   - When a context item first appears, embed its full content in question_context.
   - For later questions that rely on that context, do not duplicate it; instead, reference the originating question_id in question_dependencies.
   - If a block begins with context (table, figure, etc.) but ends with an answerable instruction, treat the entire block as a **single question**, not as a context-only node plus a fabricated sub-question.
9. possible_answers must be [] for non-multiple_choice items.
10. **Output only valid JSON** – no extra text, comments, or trailing commas.

# Reasoning Steps (internal, not in output)
1. Scan the Markdown line-by-line, detecting question boundaries and context items.
2. For each detected question, build its JSON entry, applying the above rules.
3. Insert any synthesised parents where necessary using the logic above.
4. Assemble the final "questions" array in strict source order.
5. Emit the raw JSON object and nothing else.

# Final Reminder

Return **only** the JSON object in the exact schema and order specified above.
"""



assignment_extraction_prompt_template_reasoning_v8 = """
{assignment_text}

# Role & Objective
You are a data–extraction agent.
Your task: **read the Markdown OCR of a student assessment and extract every question**, then output **only** a JSON object that follows the schema and rules below.

# Output Format (exact JSON structure)
{{
  "questions": [
    {{
      "question_id": string,
      "question": string,
      "question_type": string,
      "possible_answers": [string, …],
      "total_marks_available": int | null,
      "question_context": [
        {{
          "component_type": "text" | "table" | "chart" | "image" | "equation",
          "component": {{
            // if component_type="text"|"table"|"equation":
            "type": "text",
            "data": "…exact content…"
            // or if component_type="image"|"chart":
            // "type":"reference",
            // "reference":"image_x"
          }}
        }}
      ],
      "likely_answer_component_type": "text" | "table" | "chart" | "equation" | "image",
      "parent_question_id": string | null,
      "question_number": string,
      "question_dependencies": [string, …],
      "needs_marking": boolean
    }},
    …
  ]
}}

# Field Definitions (with examples)
- **question_id** – Full identifier exactly as printed; do *not* invent extra layers.
  *Example*: `"3.2"`, `"7(b)(ii)"`.
- **question** – Exact answerable prompt only (no context).
  *Example*: `"Explain the process of photosynthesis in detail."`.
- **question_type**: one of:
  - `short_form` (brief answers; e.g. "What is the capital of France?")
  - `long_form` (essay-style; e.g. "Discuss how globalisation affects local cultures.")
  - `multiple_choice` (with explicit options; e.g. "Which of the following is a mammal? A. Fish B. Snake C. Dog D. Bird")
  - `tf_questions` (True/False; e.g. "Water boils at 90°C. True or False?")
  - `fillup` (blanks; e.g. "The capital of France is _______.", or "Fill in this table: ...".)
  - `maths` (numeric/algebraic; e.g. "Solve for x: 2x + 3 = 7")
  - `non_question` (A question that purely introduces context or only contains a title/statement/heading, and has no answerable prompt.)
- **possible_answers** – List of the option strings for `multiple_choice`; otherwise `[]`.
  *Example*: `["A. Madrid", "B. Barcelona", "C. Seville", "D. Valencia"]`.
- **total_marks_available** – Integer parsed from marks indicators such as `(4)` or `[4 marks]`; else `null`.
- **question_context** – List of context components first introduced at *this* question.
- **likely_answer_component_type** – Anticipated student-answer format (`text`, `table`, `chart`, `equation`, `image`).
- **parent_question_id** – The `question_id` of the immediate parent question, or `null` if the question is a top-level question.
- **question_number** –
  • Top-level question → same as `question_id` (e.g. `"4"`).
  • Sub-question → just the trailing part (e.g. `"a"` for `"1a"`).
- **question_dependencies** – `question_id`s of earlier questions whose context/question text is required as context for this question, else `[]`.
- **needs_marking** – `true` if an answer is expected; `false` otherwise.

# Instructions
## Extraction & Ordering Rules
1. **Order** questions in the JSON exactly as they appear in the source.
2. Detect all main questions, sub-questions and context-only items.
3. Populate every field per the definitions above.
4. **Multiple-choice**: capture options verbatim, including their letters (“A. …”).
5. **Context Handling**
   - When a context item first appears, embed its full content in `question_context` in the format specified above.
   - For later questions that rely on that context, don't add it to their `question_context` list. Instead, list the originating `question_id` in `question_dependencies`.
6. `possible_answers` **must** be `[]` for non-`multiple_choice` items.
7. **Output only valid JSON** – no extra text, comments, or trailing commas.

# Reasoning Steps (internal, not in output)

1. Scan the Markdown line-by-line, detecting question boundaries and context items.
2. For each detected question, build its JSON entry, applying rules above.
3. Assemble the final `"questions"` array in source order.
4. Make sure the question structure reflects exactly what is in the markdown.
5. Make sure you didn't create any question which doesn't exist in the markdown or miss any question which does exist in the markdown.
6. Emit the raw JSON object and nothing else.


# Final Reminder

Return **only** the JSON object in the exact schema and order specified above.
"""

assignment_extraction_prompt_template_reasoning_v9 = """
{assignment_text}

# Role & Objective
You are a data–extraction agent.
Your task: **read the Markdown OCR of a student assessment and extract every question**, then output **only** a JSON object that follows the schema and rules below.

# Output Format (exact JSON structure)
{{
  "questions": [
    {{
      "question_id": string,
      "question": string,
      "question_type": string,
      "possible_answers": [string, …],
      "total_marks_available": int | null,
      "question_context": [
        {{
          "component_type": "text" | "table" | "chart" | "image" | "equation",
          "component": {{
            // if component_type="text"|"table"|"equation":
            "type": "text",
            "data": "…exact content…"
            // or if component_type="image"|"chart":
            // "type":"reference",
            // "reference":"image_x" (exact image_x reference from the markdown)
          }}
        }}
      ],
      "likely_answer_component_type": "text" | "table" | "chart" | "equation" | "image",
      "parent_question_id": string | null,
      "question_number": string,
      "question_dependencies": [string, …],
      "needs_marking": boolean
    }},
    …
  ]
}}

# Field Definitions (with examples)
- **question_id** – Full identifier of the question with all hierarchy markers.
  *Example*: `"3.2"`, `"7(b)(ii)"`.
- **question** – Exact answerable prompt only (no context).
  *Example*: `"Explain the process of photosynthesis in detail."`.
- **question_type**: one of:
  - `short_form` (brief answers which require at most a few of sentences; e.g. "What is the capital of France?")
  - `long_form` (essay-style which require more than a few sentences; e.g. "Discuss how globalisation affects local cultures.")
  - `multiple_choice` (with explicit options; e.g. "Which of the following is a mammal? A. Fish B. Snake C. Dog D. Bird")
  - `tf_questions` (True/False; e.g. "Water boils at 90°C. True or False?")
  - `fillup` (blanks; e.g. "The capital of France is _______.", or "Fill in this table: ...".)
  - `maths` (numeric/algebraic; e.g. "Solve for x: 2x + 3 = 7")
  - `non_question` (A question that purely introduces context or only contains a title/statement/heading, and has no answerable prompt.)
- **possible_answers** – List of the option strings for `multiple_choice`; otherwise `[]`.
  *Example*: `["A. Madrid", "B. Barcelona", "C. Seville", "D. Valencia"]`.
- **total_marks_available** – Integer parsed from marks indicators such as `(4)`, `[4]` or `[4 marks]`; else `null`.
- **question_context** – List of all context components (text, table, chart, image, equation) required to answer this question AND question context components which are initially presented at this question. None of these components should repeat the `question` field.
  You must **include all necessary context items directly in the `question_context` of every question, even if those items have appeared previously or are also used by other questions**.
  This means that **context components may and should be repeated across multiple questions whenever they are needed/presented**.
- **likely_answer_component_type** – Anticipated student-answer format (`text`, `table`, `chart`, `equation`, `image`).
- **parent_question_id** – The `question_id` of the immediate parent question, or `null` if the question is a top-level question.
- **question_number** –
  • Top-level question → same as `question_id` (e.g. `"4"`).
  • Sub-question → just the trailing part of the `question_id` (e.g. `"a"` for `"1a"`).
- **question_dependencies** – if this question is a sub-question, this is a list of all the `question_id`s of the ancestors of this question, else `[]`.
- **needs_marking** – `true` if this question has an answerable prompt; `false` otherwise.

# Instructions
## Extraction & Ordering Rules
1. **Order** questions in the JSON exactly as they appear in the source.
2. Detect all main questions, sub-questions and context-only items.
3. Populate every field per the definitions above.
4. **Multiple-choice**: capture options verbatim, including their letters (“A. …”).
5. **Context Handling**
   - Every question’s `question_context` **must contain all context components that are necessary for answering that question, even if those components first appeared earlier in the assessment or are reused across multiple questions.
   - This means that context components will often **appear multiple times across different questions**.
   - You must also include question context components which are initially presented here
   6. `possible_answers` **must** be `[]` for non-`multiple_choice` items.
7. **Output only valid JSON** – no extra text, comments, or trailing commas.

# Reasoning Steps (internal, not in output)

1. Scan the Markdown line-by-line, detecting question boundaries and context items.
2. For each detected question, build its JSON entry, applying rules above.
3. Assemble the final `"questions"` array in source order.
4. Make sure the question structure reflects exactly what is in the markdown.
5. Ensure not to have omitted any questions that appear in the markdown. If you have, ensure to add them in.
6. Emit the raw JSON object and nothing else.

# Final Reminder

Return **only** the JSON object in the exact schema and order specified above.
"""











clean_up_markdown_prompt = """
# Role and Objective
You are an expert data-extraction agent that extracts assignments from complicated markdown that you are provided with.

# Instructions
1. Remove all unecessary data from the markdown leaving just a clean assignment in markdown that a student could view.
2. Do not remove any important data such as question numbers, question texts, context, `![image_x](image_x)` markers, table contexts, etc.
3. Always write down, for every question, the *full* heirarchical identifier question number of the question. For example: if in the markdown, there is a sub question of question `1` identified as just `a` in the original markdown, you should, in the clean markdown write the question number as `1a` to show the links between questions. 
4. Structure your assignment as it appears in the markdown showing the heirarchy of the questions too.

# Output Format

Plain markdown with all of the assignment information neatened up and presented in clean markdown but with nothing important missing.

# Examples
## Example output 1

1. Use figure 1 to answer the following question. Which are longer; a hare's legs or a rabbit's legs? 
![image_1](image_1)
| Species         | Average Front Leg Length (cm) | Average Hind Leg Length (cm) |
|-----------------|------------------------------|------------------------------|
| European Rabbit | 6.5                          | 9.8                          |
| Cottontail      | 7.2                          | 10.4                         |
| Mountain Hare   | 8.0                          | 14.5                         |
| Brown Hare      | 8.5                          | 15.2                         |
| Snowshoe Hare   | 8.3                          | 14.9                         |
2. When did WW2 start?
[2 marks]
3.
3a. The capital of France is _______.
3b. The capital of Spain is _______.
3c. A food that Italy is famous for is:
A. Pizza
B. Cottage Pie
C. Fish and Chips
D. Sushi
[1 mark]

## Example output 2
1. Read through the following table:
| Name     | Age |
| -------- | --- |
| John     | 45  |
| Emily    | 32  |
| Michael  | 27  |
| Samantha | 52  |

1.1 What was the age of the oldest person in the table?
1.2 What was the age of the youngest person in the table?
1.3 What was the average age of the people in the table?
2. Snape is a friendly character. True or False:
[1]
3. Solve the following equation:
$$
x^{{2}}+3 x+3=0
$$
4. Describe the process of photosynthesis in detail.
![image_2](image_2)
The figure above shows a detailed view of a leaf with all components labeled.

# Important Notes
 - Do not add any extra text or comments to the markdown.
 - Do not remove any important information from the markdown.
 - Do not remove any of the question context (including image references, and tables) from the markdown.
"""

reduced_assignment_extraction_prompt = """
# Role and objective
You are an expert data-extraction agent that extracts assignments into JSON from markdown that you are provided.

# Instructions
1. Take each and every question and place it into its own question object in the `questions` list.
2. Populate the question object with the following fields:
  - `question_id` - the *full* identifier of the question with all hierarchy markers as it appeared in the markdown. e.g. "3.2", "7(b)(ii)", "4a", "1".
  - `question` - the exact question text only.
  - `possible_answers` - if the question is a multiple choice question, this should be a list of the option strings including the letter. e.g. ["A. ...", "B. ...", ...]; otherwise it should be an empty list.
  - `total_marks_available` - the total marks available for this question. This should be an integer parsed from the markdown. Mark indicators usually look like the following: "[4]", "[4 marks]", "(4)", etc. If there are no marks available, this should be null.
  - `question_context` - a list of all context components (text, table, chart, image, equation) required to answer this question. This should not include the question text itself. You must include all necessary context items directly in the question_context of every question, even if those items have appeared previously or are also used by other questions. This means that context components may and should be repeated across multiple questions whenever they are needed/presented. If no context needed, then this should be an empty list.
3. Return the questions in the order they appear in the markdown in the JSON object with nothing else.
4. Do not add any extra text or comments to the JSON object.

## Edge Case Handling
- If a question seems to have no `question_id` in the markdown, try to infer what the question_id should be based on the previous `question_id`s.
- For maths questions, do not move the equation to the question_context. Instead, keep it in the question field.
- If you have added context to the `question_context`, ensure to not repeat it in the `question` field.
- Do not miss any questions in the markdown. Even when it is a parent question with no answerable prompt.
- Do not include any question numbers in the question field.
- A single question can contain multiple context components. Ensure to capture these.

# Output Format
{{
  "questions": [
    {{
      "question_id": string,
      "question": string,
      "possible_answers": [string, …],
      "total_marks_available": int | null,
      "question_context": [
        {{
          "component_type": "text" | "table" | "chart" | "image" | "equation",
          "component": {{
            // if component_type="text"|"table"|"equation":
            "type": "text",
            "data": "…exact content…"
            // or if component_type="image"|"chart":
            // "type":"reference",
            // "reference":"image_x" (exact image_x reference from the markdown)
          }}
        }}
      ]
    }},
    …
  ]
}}
"""

create_relations_prompt = """
# Role and objective
You are a data expert that will create relations between questions in a hierarchical assignment JSON object you are provided with and return a JSON object.
You will modify the JSON object provided to you to add the following fields to each question object (without modifying any of the existing fields):
- `likely_answer_component_type`
- `parent_question_id`
- `question_number`
- `question_dependencies`
- `needs_marking`
- `question_type`

# Definitions
## Sub-question
- A sub-question is a question that is a child of another question. 
- A sub-question relies on the parent for context.

## Top-level question
- A top-level question is a question that is not a child of another question.
- A top-level question does not rely on any other question for context.

# Instructions
For each question in the JSON object, work out if it is a sub-question or a top-level question. 
Then follow the appropiate set of instructions that are provided below.

Instructions to follow for top-level questions:
1. Fill the question_number field with the question_id of the question.
2. Set the parent_question_id field to null.
3. Set the question_dependencies field to an empty list.

Instructions to follow for sub-questions:
1. Fill the question_number field with the trailing part of the question_id. e.g. for a question like "1a", the question_number should be "a", for a question like "1.1.3", the question_number would be "3".
2. Set the parent_question_id field to the question_id of the immediate parent question.
3. Set the question_dependencies field to a list of all the question_ids of the ancestors of this question.

Instructions to follow for all questions:
1. Set the likely_answer_component_type field to the most likely format that the student's response will be presented in based on the question text. For example, if the question indicates the student should complete a table, you would return 'table'. If the question just requires a text answer or true/false or multiple-choice answer, you would return 'text'. If you are unsure, set this value to 'text' by default. Must be one of: 'text', 'table', 'chart', 'equation', 'image'.
2. Set the needs_marking field to true if the question has an answerable prompt; otherwise set it to false.
3. Set the question_type field to "short_form" if the question is a short_form question; "long_form" if it is a long_form question; "multiple_choice" if it is a multiple_choice question; "tf_questions" if it is a true/false question; "fillup" if it is a fillup question; "maths" if it is a maths question; and "non_question" if it is a non_question question.
  - `short_form` (brief answers which require at most a few of sentences; e.g. "What is the capital of France?")
  - `long_form` (essay-style which require more than a few sentences; e.g. "Discuss how globalisation affects local cultures.")
  - `multiple_choice` (with explicit options; e.g. "Which of the following is a mammal? A. Fish B. Snake C. Dog D. Bird")
  - `tf_questions` (True/False; e.g. "Water boils at 90°C. True or False?")
  - `fillup` (blanks; e.g. "The capital of France is _______.", or "Fill in this table: ...".)
  - `maths` (A mathematical question which requires mathematical reasoning.)
  - `non_question` (A question that purely introduces context or only contains a title/statement/heading, and has no answerable prompt.) If needs_marking = false then this should be the question_type.


# Output Format (exact JSON structure)
{{
  "questions": [
    {{
      "question_id": string,
      "question": string,
      "question_type": string,
      "possible_answers": [string, …],
      "total_marks_available": int | null,
      "question_context": [
        {{
          "component_type": "text" | "table" | "chart" | "image" | "equation",
          "component": {{
            // if component_type="text"|"table"|"equation":
            "type": "text",
            "data": "…exact content…"
            // or if component_type="image"|"chart":
            // "type":"reference",
            // "reference":"image_x" (exact image_x reference from the markdown)
          }}
        }}
      ],
      "likely_answer_component_type": "text" | "table" | "chart" | "equation" | "image",
      "parent_question_id": string | null,
      "question_number": string,
      "question_dependencies": [string, …],
      "needs_marking": boolean
    }},
    …
  ]
}}

# Important Notes
- Do not add any extra text or comments to the JSON object.
- Do not modify any of the existing fields in the JSON object.
"""