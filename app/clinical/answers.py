"""Normalized button AND exact typed choices. Unrecognized text is NOT interpreted here.
Any open text must pass separately evaluated multilingual extraction and red-flag checks.
"""
from datetime import datetime
from .types import Fact
from .registry import Question

class NeedsValidatedExtraction(ValueError):
    pass

def normalized_answer(question: Question, answer, observed_at: datetime, source_id: str,
                      source_type='patient') -> Fact:
    kind=question.answer_schema['kind']
    if kind=='choice':
        answer_str=str(answer).strip().casefold()
        for choice in question.choices:
            if answer_str in (choice['code'].casefold(),choice['label_en'].casefold()):
                return Fact(code=question.fact, state=choice['fact_state'],
                  value=choice.get('fact_value'),observed_at=observed_at,
                  source_id=source_id,source_type=source_type,verification='patient_confirmed')
        raise NeedsValidatedExtraction('Unmatched typed answer: do not assume a negative finding; run safety/NLP checks')
    if kind=='nonnegative_integer':
        if isinstance(answer,bool): raise NeedsValidatedExtraction('Not a number of days')
        try:
            n=int(answer)
            if str(answer).strip()!=str(n) or n<0 or n>36500:
                raise ValueError()
        except (ValueError,TypeError):
            raise NeedsValidatedExtraction('Free text requires validated extraction/confirmation')
        return Fact(code=question.fact,state='present',value=n,observed_at=observed_at,
                source_id=source_id,source_type=source_type,verification='patient_confirmed')
    raise NeedsValidatedExtraction('Requires validated extraction before converting to clinical fact')
