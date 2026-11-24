"""Passa en gemensam diskyta till granskade källpixlar, utan kroppsskalning."""
import numpy as np

F=np.diag([1.,-1.,-1.])


def passa(t,M,fokal,frame,height,width,depth,points):
    """Endast gemensam Z-translation av kamera/person; yta och skala står kvar."""
    w,h=t['meta']['bredd'],t['meta']['hojd'];G=t['G'];V=t['V']
    rot=M[:3,:3]@G@V['kam_R'][frame]@F
    camera=M[:3,:3]@G@V['kam_C'][frame]+M[:3,3]
    surface=np.array([[-width/2,-depth/2,height],[width/2,-depth/2,height]])
    def errors(delta):
        c=(surface-camera-[0,0,delta])@rot
        uv=c[:,:2]/(-c[:,2:])*[fokal,-fokal]+[w/2,h/2]
        line=np.cross(np.r_[uv[0],1.],np.r_[uv[1],1.]);pred=np.array([-(line[0]*x+line[2])/line[1] for x,y in points])
        return pred-np.array(points)[:,1]
    lo,hi=-.25,.35
    for _ in range(40):
        a=lo+(hi-lo)/3;b=hi-(hi-lo)/3
        if np.mean(errors(a)**2)<np.mean(errors(b)**2):hi=b
        else:lo=a
    delta=(lo+hi)/2;res=errors(delta)
    return dict(status='antagen',delta_z_m=float(delta),rest_px=res.tolist(),rms_px=float(np.sqrt(np.mean(res**2))),
                metod='Diskens bortre kant mot två avlästa källpunkter. Gemensam Z-translation av person och kamera; deras inbördes projektion och skala bevaras. Diskhöjden är mallprior.',
                granser_delta_z_m=[-.25,.35])
