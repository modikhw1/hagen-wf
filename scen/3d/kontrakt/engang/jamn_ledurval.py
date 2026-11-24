"""Gemensamt ledurval för metodtabell och filmens kvalitetsmått."""
from prop_filer import andra

def tro(s):
    needle='def gravitation(v):'
    s=s.replace(needle,'''def synliga_par(ben_synliga):
    """Dolda höfter/knän utesluts; axlar och alla fingerleder behålls."""
    ok = np.ones(len(KP), bool)
    if not ben_synliga: ok[2:6] = False
    return ok


'''+needle,1)
    s=s.replace("                    reliable=np.ones(len(KP),bool)\n                    if 'ben_synliga' in s and not s['ben_synliga'][f]: reliable[:6]=[True,True,False,False,False,False]", "                    reliable=synliga_par(bool(s['ben_synliga'][f]) if 'ben_synliga' in s else True)")
    return s
andra('scen/3d/kontrakt/trohet.py',tro)
andra('scen/3d/ingest/jamn_utvardera.py',lambda s:s.replace('from trohet import KP, LED','from trohet import KP, LED, synliga_par').replace('if not rel[f]: d = np.delete(d, np.arange(2, 6))  # Bara dolda ben tas bort; fingerleder behalls.','d = d[synliga_par(bool(rel[f]))]'))
andra('scen/3d/kontrakt/test_kroppmatt.py',lambda s:s.replace("if __name__ == '__main__':",'''class Ledurval(unittest.TestCase):
    def test_fingerleder_raknas_aven_nar_benen_ar_dolda(self):
        from trohet import synliga_par, KP
        from jamn_utvardera import matt
        # Felet finns bara i fingrarna. Det gamla tabellfelet rapporterade 0.
        pose=np.zeros((3,127,8));pose[:,:,2]=-100
        target=np.tile([288.,512.],(3,70,1));target[:,KP[6:],0]+=10
        R=dict(idx=[0,1,2],FOC=np.full(3,576.),KP=target)
        result=matt(pose,np.zeros((3,3)),R,dict(bredd=576,hojd=1024),np.zeros((3,10,10)),{}, {'0':True,'1':True,'2':True},{},np.ones(3,bool),3,{},med_iou=False)
        self.assertEqual(int(synliga_par(False).sum()),44)
        self.assertAlmostEqual(result['px_median'],10.)
        self.assertAlmostEqual(result['px_p90'],10.)


if __name__ == '__main__':'''))
