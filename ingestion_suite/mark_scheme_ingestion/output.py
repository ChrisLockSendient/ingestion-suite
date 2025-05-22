from pydantic import BaseModel, Field
from typing import List, Literal
from pydantic.functional_validators import field_validator

##############################################
###    Extracted Mark Scheme Information   ###
##############################################

class ExtractedMarkSchemeInformation(BaseModel):
    question_number: str = Field(
        ...,
        description='Question number as it appears in the mark scheme image, e.g., "01.1", "05.9".'
    )
    question_text: str | None = Field(
        None,
        description='Text of the question as it appears in the mark scheme image, e.g., "What is the capital of France?"'
    )
    classification: Literal["generic", "levelled", "rubric"] = Field(
        ...,
        description='Classification of the mark scheme: "generic", "levelled", or "rubric".'
    )
    mark_scheme_information: str = Field(
        ...,
        description='Exact transcription of the entire question’s mark scheme, including all instructions, descriptors, and content.'
    )
    marks_available: int | None = Field(
        None,
        description='Marks available for the question as indicated in the mark scheme.'
    )


class ExtractedMarkSchemesInformationWrapper(BaseModel):
    mark_schemes: List[ExtractedMarkSchemeInformation] = Field(
        ...,
        description='List of mark scheme objects extracted from a given image or document.'
    )

# ##############################################
# ###     Generic Mark Scheme Model          ###
# ##############################################

class MarkSchemeCriterionModel(BaseModel):
    """Represents a criterion for marking a question."""

    mark_scheme_criterion: str
    """The criterion for marking the question."""
    marks_available: int
    """The marks available for the criterion."""
    marking_difficulty: int
    """The difficulty of marking the criterion."""
    key_points: list[str] = []
    """The key points for the criterion."""

    @field_validator("marking_difficulty")
    @classmethod
    def validate_marking_difficulty(cls, value):
        if not 0 <= value <= 3:
            raise ValueError("marking_difficulty must be between 0 and 3 (inclusive).")
        return value


class MarkSchemeBaseModel(BaseModel):
    """Represents a mark scheme base model."""

    total_marks_available: int | None = None
    """The total marks available for the question."""
    criteria: list[MarkSchemeCriterionModel] | None = None
    """The criteria for marking the question."""
    equivalents_or_follow_through_allowed: bool | None = None
    """Used for maths questions mark schemes to indicate if equivalents or follow through is allowed"""


##############################################
###     Leveled Mark Scheme Model          ###
##############################################

class LeveledMarkSchemeModel(BaseModel):
    """Represents a leveled mark scheme."""

    level: str = Field(description="A string describing the level in the mark scheme. This is usually a number but should be what it states in the mark scheme image.")
    """The level of the mark scheme."""
    upper_mark_bound: int = Field(description="The upper mark bound for the mark scheme level.")
    """The upper mark bound for the mark scheme."""
    lower_mark_bound: int = Field(description="The lower mark bound for the mark scheme level.")
    """The lower mark bound for the mark scheme."""
    skills_descriptors: list[str] = Field(description="A list containing the skills descriptors for a mark scheme level.")
    """List of skill descriptors"""
    indicative_standard: str | None = Field(description="Examples of quality of answer for a given level")
    """Examples of quality of answer"""


class ObjectiveMarkSchemeModel(BaseModel):
    """Represents a mark scheme for an objective."""

    objective: str = Field(description="The objective for the mark scheme. ie. AO1")
    """The objective for the mark scheme. ie. AO1"""
    mark_scheme: list[LeveledMarkSchemeModel] = Field(description="The mark scheme for the objective.")
    """The mark scheme for the objective."""
    guidance: str | None = Field(description="Any general marking guidance provided in the source, such as how to award marks or interpret responses, otherwise null")
    """Any general marking guidance provided in the source, such as how to award marks or interpret responses, otherwise null"""
    indicative_content: str | None = Field(description="Examples of content that could be used to answer the question, otherwise null")
    """Examples of content that could be used to answer the question, otherwise null"""
    weight: float | None = Field(description="The decimal weight of the assessment objective as a ratio of the total marks available for the question.")
    """The weight of the assessment objective"""

# ##############################################
# ###     Rubric Mark Scheme Model           ###
# ##############################################

class RubricMarkSchemeModel(BaseModel):
    """Represents a rubric mark scheme."""

    rubric: List[ObjectiveMarkSchemeModel] = Field(description="The rubric for the mark scheme.")
    """The rubric for the mark scheme."""

# ##############################################
# ###     Ingested Mark Scheme Model         ###
# ##############################################

class IngestedMarkSchemeModel(BaseModel):
    """Represents a mark scheme that has been ingested."""

    type: Literal["generic", "levelled", "rubric"] = Field(description="The type of mark scheme.")
    """The type of mark scheme."""
    question_number: str = Field(description="The question number for the mark scheme.")
    """The question number for the mark scheme."""
    question_text: str | None = Field(description="The text of the question for the mark scheme.")
    """The text of the question for the mark scheme."""
    marks_available: int | None = Field(description="The marks available for the question.")
    """The marks available for the question."""
    mark_scheme_information: str = Field(description="The mark scheme information for the question.")
    """The mark scheme information for the question."""
    mark_scheme: ObjectiveMarkSchemeModel | MarkSchemeBaseModel | RubricMarkSchemeModel = Field(description="The mark scheme for the question.")
    """The mark scheme for the question."""

class IngestedMarkSchemesModel(BaseModel):
    """Represents a list of ingested mark schemes."""

    mark_schemes: List[IngestedMarkSchemeModel] = Field(description="The list of ingested mark schemes.")
    """The list of ingested mark schemes."""

