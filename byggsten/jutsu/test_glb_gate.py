import json
import tempfile
from pathlib import Path
import unittest
from glb_gate import audit_gltf,require_current_export,file_hash


def fixture():
    return {'scene':0,'scenes':[{'nodes':[0]}],
            'nodes':[{'name':'RIG_1_full_huvud','mesh':0,'scale':[.1,.12,.1]}],
            'meshes':[{'primitives':[{'attributes':{'POSITION':0}}]}],
            'accessors':[{'min':[-1,-1,-1],'max':[1,1,1]}]}


class GLBGateTests(unittest.TestCase):
    def test_valid_head(self):
        self.assertTrue(audit_gltf(fixture())['passed'])

    def test_regression_hidden_beat_at_origin(self):
        doc=fixture(); doc['nodes'].append({'name':'RIG_1_beat_huvud','mesh':0});doc['scenes'][0]['nodes'].append(1)
        r=audit_gltf(doc)
        self.assertFalse(r['passed'])
        self.assertTrue(any('exceeds' in e for e in r['errors']))
        self.assertTrue(any('alternative' in e for e in r['errors']))

    def test_parent_scale_counts(self):
        doc=fixture();doc['nodes'].append({'scale':[10,10,10],'children':[0]});doc['scenes'][0]['nodes']=[1]
        self.assertFalse(audit_gltf(doc)['passed'])

    def test_missing_visibility_channel(self):
        doc=fixture();doc['nodes'][0]['extras']={'pipe_visibility':'scale-zero-constant-v1'}
        self.assertFalse(audit_gltf(doc)['passed'])
        doc['animations']=[{'channels':[{'target':{'node':0,'path':'scale'}}]}]
        self.assertTrue(audit_gltf(doc)['passed'])

    def test_constant_visibility_can_be_optimized(self):
        doc=fixture();doc['nodes'][0]['extras']={'pipe_visibility':'scale-zero-constant-v1','pipe_visibility_animated':False}
        self.assertTrue(audit_gltf(doc)['passed'])

    def test_split_animation_is_rejected(self):
        doc=fixture();doc['animations']=[{'channels':[]},{'channels':[]}]
        self.assertFalse(audit_gltf(doc)['passed'])

    def test_stale_delivery_is_blocked(self):
        with tempfile.TemporaryDirectory() as folder:
            out=Path(folder);(out/'preview').mkdir()
            blend=out/'preview/scene.blend';glb=out/'preview/delivery.glb'
            blend.write_bytes(b'scene');glb.write_bytes(b'export')
            report={'passed':True,'roundtrip_passed':True,'blend_sha256':file_hash(blend),'glb_sha256':file_hash(glb)}
            (out/'glb_local_audit.json').write_text(json.dumps(report))
            require_current_export(out)
            blend.write_bytes(b'changed scene')
            with self.assertRaises(RuntimeError):require_current_export(out)


if __name__=='__main__': unittest.main()
