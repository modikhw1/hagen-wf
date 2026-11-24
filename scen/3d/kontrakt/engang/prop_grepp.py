"""Grepppunkt även utan mätregion, och köttet stöds av vågbrickan."""
from prop_filer import andra

andra('scen/3d/kontrakt/propplan.py',lambda s:s.replace("for o in plan.get('props',[]):", "for o in sorted(plan.get('props',[]), key=lambda x: x['prop_typ']!='weighing_scale'):",1)
    .replace("fast_i_hand(hp,R,offset+grip,grip)","fast_i_hand(hp,R,offset+grip if center is not None else offset,grip)")
    .replace("            best=None;c,ray=sikt(keys[uref],center,w,h)", "            if p.get('yta','').startswith('prop_'):\n                parent=next((x for x in plan.get('props',[]) if x['id']==p['yta'] and x['scen']==o['scen'] and x.get('nycklar')),None)\n                if parent:\n                    pmatrix=np.array(parent['nycklar'][0]['matris']);dims=np.array(parent['matt_m'])\n                    candidates=[dict(id=parent['id']+':bricka',pos_m=(pmatrix[:3,3]+pmatrix[:3,:3]@np.array([0,0,-.25*dims[2]])).tolist(),matt_m=[1.05*dims[0],1.05*dims[1],.05*dims[2]],rotation_rad=[0,0,0])]\n            best=None;c,ray=sikt(keys[uref],center,w,h)"))
andra('scen/3d/kontrakt/kalla_prop.py',lambda s:s.replace("surface='bord' if clip=='notan' else 'disk'", "surface='bord' if clip=='notan' else 'disk'\n                if clip=='b' and raw['id']=='o1' and sid in ('s8','s9','s10','s11'): surface='prop_o2'"))
andra('scen/3d/kontrakt/test_props.py',lambda s:s.replace("    def test_banken_har_grepp_och_ursprung(self):", '''    def test_upplost_prop_foljer_hand_och_bankgrepp(self):
        from gemensamt import HIT
        from trohet import IX
        with tempfile.TemporaryDirectory(prefix='prop_hand_',dir=HIT/'ut') as td:
            path=Path(td);np.savez(path/'s.npz',inom=np.ones(3,bool));np.savez(path/'v.npz',kam_C=np.zeros((3,3)))
            o=ny(dict(ny_id='mat',typ='meat_cut',faste=dict(person='A',led='l_wrist_twist',hand='vanster')));o.update(scen='s1',synlig_ut=[0,3])
            pm=dict(id='A',rorelse=str(path/'s.npz'));sc=dict(id='s1',ut=[0,3],lokal_start=0,varld=str(path/'v.npz'),personer=[pm])
            keys=[dict(matris=np.eye(4).tolist(),lins_mm=36)]*3
            plan=dict(kallbild_bredd=576,utdata=dict(bredd=576,hojd=1024),scener=[sc],renderkamera=dict(nycklar=keys),props=[o],objekt=[],kvalitet={})
            def pose(sc,pm,f,stod,data):
                p=np.zeros((127,8));p[:,6]=1;p[IX['l_wrist_twist'],:3]=[10*f,0,100]
                return p,np.eye(3),np.zeros(3)
            with patch('propplan.ruta_pose',side_effect=pose):los(plan)
            for f,key in enumerate(o['nycklar']):
                m=np.array(key['matris']);np.testing.assert_allclose(m[:3,3]+m[:3,:3]@o['bank']['grepp'],[f*.1,0,1.])

    def test_banken_har_grepp_och_ursprung(self):'''))
