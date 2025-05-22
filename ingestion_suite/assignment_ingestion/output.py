from typing import List, Literal
from pydantic import BaseModel, Field, model_validator

from datetime import datetime
from typing import Generic, TypeVar

from enum import Enum


class ComponentTextModel(BaseModel):
    """Represents a text component for a question."""

    type: Literal["text"] = "text"
    """The type of context for the question."""
    data: str = Field("Contains the actual text of the context.")
    """The context for the question."""


class ComponentReferenceModel(BaseModel):
    """Represents a reference to another component stored in common_components."""

    type: Literal["reference"] = "reference"
    """The type of context for the question."""
    reference: str = Field("This is the string that contains a reference to an image reference. e.g. 'image_1'")
    """String that is an identifier to component in common_components."""


class ComponentType(str, Enum):
    """The type of component for a question."""

    TEXT = "text"
    TABLE = "table"
    CHART = "chart"
    IMAGE = "image"
    EQUATION = "equation"
    REFERENCE = "reference"


_ComponentDataModels = TypeVar(
    "_ComponentDataModels",
    ComponentTextModel,
    ComponentReferenceModel,
    ComponentTextModel | ComponentReferenceModel,
)

class ComponentModel(BaseModel, Generic[_ComponentDataModels]):
    """Represents a component for a question."""

    component_type: ComponentType = Field("The type of context for the question chosen from: 'text', 'table', 'chart', 'image', 'equation', 'reference'.")
    """The type of context for the question."""
    component: _ComponentDataModels
    """The context for the question."""

    @model_validator(mode="after")
    def reference_validator(self):
        if self.component_type == ComponentType.REFERENCE:
            if not isinstance(self.component, ComponentReferenceModel):
                raise ValueError(
                    "If component_type is reference, component must be ComponentReferenceModel"
                )
        else:
            if isinstance(self.component, ComponentReferenceModel):
                raise ValueError(
                    "If component_type is not reference, component must be a ComponentTextModel"
                )
        return self


class OneQuestionModelV3(BaseModel):
    """The output format (of a single question) for first pass of a teacher-uploaded assessment to the LLM."""

    question_id: str = Field(
        description="The question number as it appears in the assessment (it could be a number or letter or both). If it is a sub-question e.g. 'b.' after question 2, then it should be written as '2b. Another example: 'i.' after question 2a. should be written as '2ai.'"
    )
    question: str = Field(
        description="The question text. Include any text that sets the scene for the question but NOT extracts or sources of text. It MUST not include text in tables, charts or images. If it's a multiple choice question, it must not include the possible answers as these will populate the possible_answers field. This could also be a non-question question which is not a question but a statement or instruction that does not require an answer. Usually adds context for its children questions."
    )
    question_type: Literal[
        "short_form", "long_form", "multiple_choice", "tf_questions", "fillup", "maths", "non_question"
    ] = Field(description="""The question type for that question number. The question type must be one of either:
- 'short_form' (the question requires just a short answer between one word and a few sentences).
- 'long_form' (the question requires a longer answer, typically a large number of sentences or an essay)
- 'multiple_choice' (the question requires the student to select one or more answers from a set of options).
- 'tf_questions' (the question requires the student to answer true or false).
- 'fillup' (the question requires the student to fill in the blank, which may be at the start, end or middle of the question - and may involve multiple blanks). Often indicated by missing words in a sentence or phrase.
- 'maths' (the question requires the student to solve a mathematical problem using numbers or equations).
- 'non_question' (the question is not a question but a statement or instruction that does not require an answer. Usually adds context for its children questions).

As an example a short_form question type might be:
"What is the capital of France?" or "State 2 causes of the First World War." or "Briefly describe the heart's function [2 marks]."
A long_form question might be:
"Explain the causes of the American Civil War." or "Write an essay on the importance of education."
A multiple_choice question might be:
"Which of the following is a mammal? A. Fish B. Snake C. Dog D. Bird"
A true or false question might be:
"The moon orbits the Earth. True or False?"
A fillup question might be:
"The capital of France is _______" or "______ and _____ is a traditional British dish served with vinegar and mushy peas."
A maths question might be:
"What is x(x + 4) expanded out?" or "How much change does a customer get if they pay £20 for an item that costs £15.50?"
A non_question question might be:
"Source X is a diagram showing the known particles and Source Y is a table of known lepton masses."
or
"The student claps loudly once.
After a short time, they hear a second clap. The second clap is quieter."

Use your best judgement, but if you are really unsure about the question type, set it to be 'short_form'.""")
    possible_answers: List[str] = Field(
        description="The possible answers for that question (only to be filled for multiple choice questions - otherwise return an empty list). Include any letters or numbers that precede the option e.g. 'A. option1', 'B. option2', etc. If there is no text associated with the answer options, you must choose the following default values e.g. 'A. option 1', 'B. option 2', 'C. option 3', etc."
    )
    total_marks_available: float | None = Field("""The number of marks available for that question, usually indicated in brackets near the question number or question text. If not present, just return null.""")
    question_context: List[ComponentModel] = Field("""The context(s) (sources of information like figures/tables/extracts, etc) that are associated with this question. Any image context must be stored as a reference component model.""")
    likely_answer_component_type: ComponentType = Field(
        description="The most likely format that the student's response will be presented in based on the question text. For example, if the question indicates the student should complete a table, you would return 'table'. If the question just requires a text answer or true/false or multiple-choice answer, you would return 'text'. If you are ever unsure, set this value to 'text' by default."
    )

    # NEW FIELDS

    parent_question_id: str | None = Field(
        default=None,
        description=(
            "The question_id of the immediate parent question, if this is a sub-question, otherwise return null."
            "This supports hierarchy and context inheritance from parent to child. "
            "Example: if this question is '2bii' (question ii under 2b), then parent_question_id='2b'."
            "Example: if this question is '6.4.2' (question 2 under question 4 which is under question 6), then parent_question_id='6.4'."
        )
    )

    question_number: str | None = Field(
        default=None,
        description=(
            "The label of the current question without the parent question number.\n"
            "Examples: question_number='a' for question_id='1a' and parent_question_id='1'.\n"
            "question_number='ii' for question_id='4bii' and parent_question_id='4b'.\n"
            "question_number='3' for question_id='4.3' and parent_question_id='4'.\n"
        )
    )

    question_dependencies: List[str] = Field(
        default_factory=list,
        description=(
            "List of question_ids that this question depends on for context (actual context objects or in the question text)."
            "Used when this question uses context which is created in a parent question or needs the parent question's question text as context."
            "Example: if 2bii relies on context from question with question_id of 2, then question_dependencies=['2']."
            "Example: if 1.6.3 relies on context from questions with question_id of 1.6 and 1, then question_dependencies=['1', '1.6']."
            "Example: if 3b follows from 3 but doesn't rely on any context from question 3, then question_dependencies=[]."
            "\nIf no dependencies exist then return an empty list."
        )
    )

    # is_leveled_marking: bool = Field(
    #     default=None,
    #     description=(
    #         "This determines if a question is to be marked by a levelled rubric."
    #         "This is set true for an essay based question or a question which could be seen as subjective or a question which is a quality-of-answer question rather than a looking for information question."
    #         "Example: A question such as 'Discuss the factors which lead to WW2.' would set is_leveled_marking=True."
    #         "Example: A question such as 'How does the writer use language and structure to describe Hartop?' would set is_leveled_marking=True."
    #         "Example: A question such as 'It is the people who have extraordinary skill, courage and determination who deserve to be famous, not those who have good looks or lots of money or behave badly.\n\nWrite a letter to the editor of a newspaper in which you argue your point of view in response to this statement.' would set is_leveled_marking=True."
    #     )
    # )

    needs_marking: bool = Field(
        default=True,
        description=(
            "False if the question_text is structural or introductory "
            "and should not be marked directly.\n"
            "This effectively shows if there is meant to be an answer to the question or not."
            "Example: For question_text like 'The diagram shows a method used to grow pure cultures...', "
            "set needs_marking=False, since marking only occurs in this question's sub-questions."
            "Example: question_text='Many different species can live together in the same habitat.'"
            "set needs_marking=False, since marking occurs in this question's sub-questions."
        )
    )


    class Config:
        extra = "forbid"

class QuestionModelV3(BaseModel):
    questions: List[OneQuestionModelV3]




class OneQuestionModelHalfComplete(BaseModel):
    """The first stage of exraction question format"""

    question_id: str
    question: str
    question_type: Literal[
        "short_form", "long_form", "multiple_choice", "tf_questions", "fillup", "maths", "non_question"
    ]
    possible_answers: List[str]
    total_marks_available: int | None
    question_context: List[ComponentModel]


    class Config:
        extra = "forbid"

class QuestionModelHalfComplete(BaseModel):
    questions: List[OneQuestionModelHalfComplete]

