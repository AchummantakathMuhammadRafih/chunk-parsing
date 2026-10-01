from presidio_analyzer import AnalyzerEngine, PatternRecognizer, Pattern
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig

analyzer = AnalyzerEngine()
anonymizer = AnonymizerEngine()

# Built-in LOCATION only catches cities/countries, so add a street-address pattern
street_recognizer = PatternRecognizer(
    supported_entity="STREET_ADDRESS",
    patterns=[Pattern(
        name="street",
        regex=r"\b\d{1,5}\s+(?:\w+\s){1,4}(?:street|st|avenue|ave|road|rd|boulevard|blvd|lane|ln|drive|dr|court|ct)\b\.?",
        score=0.6,
    )],
)
analyzer.registry.add_recognizer(street_recognizer)

ENTITIES = ["PERSON", "EMAIL_ADDRESS", "PHONE_NUMBER", "LOCATION", "STREET_ADDRESS"]

STAR = OperatorConfig("mask", {"masking_char": "*", "chars_to_mask": 1000, "from_end": False})

OPERATORS = {
    "PERSON":         STAR,
    "EMAIL_ADDRESS":  STAR,
    "PHONE_NUMBER":   STAR,
    "LOCATION":       STAR,
    "STREET_ADDRESS": STAR,
    "DEFAULT":        STAR,
}

def mask(text: str) -> str:
    results = analyzer.analyze(text=text, language="en", entities=ENTITIES, score_threshold=0.4)
    return anonymizer.anonymize(text=text, analyzer_results=results, operators=OPERATORS).text

print(mask('''
Source [40ha] (UsabilityTestingOfMedicalDevices_2014-Ch12, page 1):
Should User Interface Designers Conduct Usability Tests of Their Own Designs?
Can You Modify a Test in Progress?
During formative testing, you can adjust the evaluated design or your testing approach to make testing more productive (i.e., help you identify and address as many usability issues as possible) as long as enough sessions remain to properly evaluate the incorporated changes.
![](/api/v1/documents/images/raw?blobPath=images%2Fdefault%2FUsabilityTestingOfMedicalDevices_2014-Ch12%2F611b62c7-bd1a-4a3c-8efe-192a7b3ef942.png)
Adjusting a summative test midcourse is also possible but more complicated due to the need to ensure a sufficient sample size and maintain methodological consistency among test sessions.
Consider this usability testing scenario:
1. You have completed a third (4 of 12) of the sessions in a formative usability test of a prototype medical device.
2. The same usability issue has arisen during each of the four test sessions, and it is a major one.
3. You think a quick change to the prototype (e.g., modifying the text in an on-screen instruction, refining an icon, or adding a small plastic tubing clip to a hardware model) will resolve the usability problem.
Is it okay to make the quick change? We think so, noting that formative usability testing is supposed to be a practical exercise to identify design strengths and opportunities for improvement. It is not supposed to be about matching the high standard of methodological purity required for clinical trials, for example. You just need to make sure that any midcourse adjustments to your testing approach, including changing the nature of the stimuli (e.g., revising a prototype), do not lead to false findings because you are drawing conclusions based on the data from too few test sessions. You also need to obtain the approval of the project stakeholders and properly document midcourse adjustments in the test report, comparing and contrasting the data from the participants who interacted with the device before and after you implemented the modification. If your test required IRB approval (see “Do Usability Test Plans Require Institutional Review Board Approval?” in Chapter 7), take care not to make changes that might expose test participants to new risks.
As stated in “How Do You Set Expectations?” in Chapter 5, Erin Davis it can be perilous to draw conclusions from one test session. Accordingly, it is critical that usability specialists collaborate with engineers, designers, and project managers, drawing together the domain and experiential knowledge necessary to assess whether a given issue will cause problems for other users. In some cases, an observed use error might be an artifact of a particular participant’s lack of attention to detail, for example.
In the scenario described, in which two-thirds of the test sessions were still to come, we would be comfortable modifying the prototype and collecting additional data from the subsequent eight test participants. We would be hesitant to make the change if we had completed most of the test sessions and had only a few sessions left
'''))
# Contact [PERSON] at [EMAIL] or [PHONE]. He lives at [ADDRESS], [ADDRESS].