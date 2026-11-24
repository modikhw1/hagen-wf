"""Geometry regressions: handedness, visibility and distance semantics."""
import unittest
import numpy as np
from rum import gravity, object_distance, plane_ransac, project
from rum_verify import segment_hits_box


class GeometryTests(unittest.TestCase):
    def test_rotated_world_clearance_and_occlusion(self):
        u=np.array([.1,-.99,.04]);u/=np.linalg.norm(u);G=gravity(u)
        np.testing.assert_allclose(G@u,[0,0,1],atol=1e-10)
        np.testing.assert_allclose(G@G.T,np.eye(3),atol=1e-10)
        obj=dict(centre=(np.array([0,2,1])@G).tolist(),size=[2,1,2],yaw=0)
        roots=np.array([[0,0,0],[0,2,0],[2,2,0]])
        np.testing.assert_allclose(object_distance(roots,obj,G),[1.5,0,1])
        camera=np.array([0,0,1.5])@G;targets=np.array([[0,4,.5],[0,4,3.5],[5,4,.5]])@G
        self.assertEqual(segment_hits_box(camera,targets,obj,G).tolist(),[True,False,False])

    def test_horizontal_ransac_rejects_vertical_wall(self):
        rng=np.random.default_rng(7)
        wall=np.c_[np.ones(1000),rng.uniform(-3,3,1000),rng.uniform(-2,2,1000)]
        floor=np.c_[rng.uniform(-3,3,(500,2)),np.full(500,-1.4)]+rng.normal(0,.002,(500,3))
        n,d,inside=plane_ransac(np.vstack([wall,floor]),'horizontal',reference=-1.4)
        self.assertLess(np.degrees(np.arccos(n[2])),1)
        self.assertAlmostEqual(d,-1.4,delta=.01)
        self.assertGreater(inside.sum(),490)

    def test_signed_projection_of_infinite_line(self):
        V={'kam_C':np.zeros((1,3)),'kam_R':np.eye(3)[None]}
        uv,z=project(np.array([[1.,2.,4.],[-1.,-2.,-4.]]),0,V,100,(200,300))
        np.testing.assert_allclose(uv,[[125,200],[125,200]])
        self.assertEqual(z.tolist(),[4,-4])


class MattaGrupperOchRutor(unittest.TestCase):
    def test_grupper_ur_matta_par_och_pargrans(self):
        import rum_grupper as g
        self.assertEqual(g.nollgrans([10, 20, 30, 38]), max(15., float(np.percentile([10, 20, 30, 38], 99))))
        self.assertEqual(g.nollgrans([]), 15.)
        self.assertEqual(g.pargrans(40., 20), 40.); self.assertEqual(g.pargrans(40., 60), 90.)           # kakelrika par får högre gräns
        bra = dict(F_inl=543, H_inl=511, R_grader=2.3, andel_rutpar_over_grans=1.0)
        self.assertEqual(g.ar_matt(bra, 90.), ('matt', []))
        st, orsak = g.ar_matt(dict(F_inl=104, H_inl=79, R_grader=104., andel_rutpar_over_grans=.12), 90.)      # kakelalias: rotationen är osammanhängande
        self.assertEqual(st, 'ingen mätbar koppling'); self.assertTrue(any('rotation' in o for o in orsak)); self.assertTrue(any('hälften' in o for o in orsak))
        self.assertEqual(g.ar_matt(dict(F_inl=30, H_inl=29, R_grader=1., andel_rutpar_over_grans=1.), 90.)[0], 'ingen mätbar koppling')
        par = [dict(par=['S1', 'S2'], status='matt'), dict(par=['S2', 'S3'], status='matt'), dict(par=['S4', 'S5'], status='ingen mätbar koppling')]
        grupper, utan = g.bilda_grupper(['S1', 'S2', 'S3', 'S4', 'S5', 'S6'], par)
        self.assertEqual(grupper, [['S1', 'S2', 'S3']]); self.assertEqual(utan, ['S4', 'S5', 'S6'])

    def _seg(self, fynd_per_tagning):
        return dict(prompter=dict(disk='butcher counter', vag='electronic scale'),
                    resultat=[dict(id=f'{t}_{i}', bredd=100, hojd=200, fynd=f) for t, fl in fynd_per_tagning.items() for i, f in enumerate(fl)])

    def test_rutor_tre_kontroller_overlapp_homografi_och_null(self):
        import rum_rutor as r
        f = lambda e, b, p: dict(etikett=e, poang=p, dino_box_px=b)
        seg = self._seg({'S1': [[f('counter', [0, 100, 100, 200], .6), f('scale', [0, 10, 40, 60], .5)]] * 2,                      # disk i nederkant, våg i övre vänstra
                         'S2': [[f('counter', [0, 20, 60, 120], .4), f('scale', [0, 20, 60, 120], .7)]] * 2,                       # disk och våg sammanfaller
                         'S3': [[f('counter', [0, 100, 100, 200], .6)]] * 2})                                                    # vågen hittas inte
        rutor, null = r.rutor_ur_seg(seg, seg['prompter'])
        self.assertIn('vag', rutor); self.assertNotIn('S3', rutor['vag'])
        self.assertEqual([(n['element'], n['tagning']) for n in null], [('vag', 'S3')]); self.assertIn('null', null[0]['orsak'])
        stopp = r.kontrollera_overlapp(rutor)
        self.assertEqual([(s['element'], s['tagning']) for s in stopp], [('disk', 'S2')])             # lägst poäng stoppas
        self.assertIn('sammanfaller', stopp[0]['orsak'])
        # homografiöverföring: identitet godkänner lika rutor, men en förskjutning på 40 % av bilden stoppar båda tagningarna
        rutor2 = {'disk': {'S1': dict(box_2d=[500, 0, 1000, 1000], poang=.5, antal=2), 'S2': dict(box_2d=[505, 0, 1000, 1000], poang=.5, antal=2),
                           'S3': dict(box_2d=[0, 0, 200, 300], poang=.5, antal=2)}}
        ident = lambda a, b: np.eye(3)
        s_ok, _ = r.kontrollera_homografi(rutor2, [['S1', 'S2']], ident); self.assertEqual(s_ok, [])
        s_fel, kontr = r.kontrollera_homografi(rutor2, [['S1', 'S3']], ident)
        self.assertEqual(sorted((s['tagning'], s['kontroll']) for s in s_fel), [('S1', 'homografi'), ('S3', 'homografi')]); self.assertTrue(all(k['iou'] < .25 for k in kontr))
        kvar = r.tillampa(rutor2, s_fel); self.assertEqual(list(kvar['disk']), ['S2'])
        D = dict(platser=dict(disk=dict(typ='bord', bild=dict(tagning='S1', box_2d=[1, 2, 3, 4]), bilder=[dict(tagning='S1', box_2d=[1, 2, 3, 4])])), foremal={})
        ut = r.skriv_deklaration(D, kvar, s_fel, [], 'prov')
        self.assertEqual([b['tagning'] for b in ut['platser']['disk']['bilder']], ['S2']); self.assertEqual(ut['platser']['disk']['bild']['tagning'], 'S2')
        self.assertEqual(len(ut['rutor_stoppade']), 2)


if __name__=='__main__':unittest.main()
