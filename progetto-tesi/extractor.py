import re
import time
import string

import en_core_web_md
import spacy
from spacy import displacy
from person import Person

import scraper


def extract_program_committees(text):
    start_time = time.time()
    
    program_headings = ["program committee", "program chair", "program commission"]
    headings = ["committee", "chair", "commission"]

    # gets all the sections referring to a program committee
    program_indexes = [text.lower().find(p) + len(p) for p in program_headings if text.lower().find(p) > -1]
    program_committees = list()
    for start in program_indexes:
        next_programs = [text[start:].lower().find(p) for p in headings if text[start:].lower().find(p) > -1]
        next_title = min(next_programs) if len(next_programs) else len(text)
        end = text.rfind("\n", 0, next_title)
        # re-polish html to avoid misprints from the substring process
        program_committees.append(scraper.polish_html(text[start:start+end]))

    print('Extraction of program committee: ', time.time() - start_time)
    return program_committees


def ner(text):
    start_time = time.time()
    nlp = en_core_web_md.load()
    print('Loading NER: ', time.time() - start_time)

    results = list()
    
    for program_committee in text:
        ner_results = []
        step = 0
        text_lines = program_committee.splitlines()
        # run NER every `step` lines and check if the result set is significantly reduced.
        while True:
            start_time = time.time()
            people = 0
            # NER multiprocessing on single lines
            lines = [l for i, l in enumerate(text_lines) if len(l) >= 4 and i % (step + 1) == 0]
            for doc in nlp.pipe(lines, n_threads=16, batch_size=10000):
                people = people + 1 if len([ee.text for ee in doc.ents if ee.label_ == 'PERSON']) else people

            ner_results.append(people)
            print('NER results with step', step + 1, ':  ', ner_results[step], time.time() - start_time)
            # 10%: threshold over which we can say the NER lost a significant amount of names
            if(ner_results[step]) < 0.9 * max(ner_results):
                break
            step += 1

        # run regex on the right `step` set
        regex = re.compile(r"^\W*([\w\. '’-]+)", re.MULTILINE)
        # results.append([m.group() for m in regex.finditer("\n".join(program_committee.splitlines()[::step]))])

        for i in range(0, len(text_lines), step):
            name = regex.search(text_lines[i]).group(1).strip()
            if step == 1:
                affiliation = text_lines[i].replace(name, "").strip(string.punctuation + " ")            
            else:
                affiliation = ', '.join(lines[(i + 1):(i + 1 + step - 1)])
            results.append(Person(name, affiliation))

    return [res_item for res_item in results]
