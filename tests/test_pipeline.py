import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'skills/grounded-resume/scripts'))
from resume_lib import build_evidence_index, prepare_plan, CONTENT_POLICY_VERSION
from compose_resume import compose
from finalize_resume_review import check_bundle
from validate_tailoring import validate


class PipelineTests(unittest.TestCase):
    def setUp(self):
        self.index = build_evidence_index(ROOT/'examples/profile.json')
        self.plan = prepare_plan((ROOT/'examples/job.txt').read_text(encoding='utf-8'), self.index, 'Example', 'Data Analyst', 'demo')
        self.template = (ROOT/'skills/grounded-resume/assets/resume-template.tex').read_text(encoding='utf-8')

    def test_compose_and_unsupported_skills(self):
        tex = compose(self.plan, self.index, self.template)
        self.assertIn('Alex Example', tex)
        self.assertNotIn('@@', tex)
        self.assertIn('AWS', self.plan['jd']['analysis']['missing_terms'])
        self.assertNotIn('AWS', tex)
        self.assertEqual(self.plan['jd']['status'], 'unverified')

    def test_unsupported_number_rejected(self):
        self.plan['entries'][0]['bullets'][0]['final_text'] += ' Saved 999999 dollars.'
        with self.assertRaises(ValueError):
            compose(self.plan, self.index, self.template)

    def test_wrong_employer_rejected(self):
        self.plan['entries'][0]['bullets'][0] = copy.deepcopy(self.plan['entries'][1]['bullets'][0])
        with self.assertRaisesRegex(ValueError, 'wrong entry'):
            compose(self.plan, self.index, self.template)

    def test_fixed_fact_rejected(self):
        self.plan['fixed']['contact']['name'] = 'Other Person'
        with self.assertRaises(ValueError):
            compose(self.plan, self.index, self.template)

    def test_old_source_rejected(self):
        self.plan['evidence_index_sha256'] = 'old'
        with self.assertRaises(ValueError):
            compose(self.plan, self.index, self.template)

    def test_unsupported_skill_rejected(self):
        self.plan['skill_groups'][0]['values'].append('AWS')
        with self.assertRaisesRegex(ValueError, 'Unsupported skill'):
            compose(self.plan, self.index, self.template)

    def test_automated_validation_is_not_ready(self):
        tex = compose(self.plan, self.index, self.template)
        result = validate(self.plan, self.index, tex, 'Education Technical Skills Professional Experience Selected Projects ' + '•'*30)
        self.assertFalse(result['application_ready'])

    def test_modified_artifact_invalidates_review(self):
        with tempfile.TemporaryDirectory() as folder:
            paths = {}
            hashes = {}
            for key in ('pdf','tex','plan','layout','preview_png'):
                path = Path(folder)/key
                path.write_text('original')
                paths[key] = str(path)
                hashes[key] = hashlib.sha256(path.read_bytes()).hexdigest()
            qa = {'status':'PASS','content_policy_version':CONTENT_POLICY_VERSION,
                  'artifacts':paths,'artifact_sha256':hashes,
                  'generator_sources':{paths['tex']:hashes['tex']},
                  'source_files':{paths['plan']:hashes['plan']},
                  'visual_review':{'status':'PASS','pdf_sha256':hashes['pdf']}}
            check_bundle(qa)
            Path(paths['pdf']).write_text('modified')
            with self.assertRaises(ValueError):
                check_bundle(qa)

if __name__ == '__main__':
    unittest.main()
