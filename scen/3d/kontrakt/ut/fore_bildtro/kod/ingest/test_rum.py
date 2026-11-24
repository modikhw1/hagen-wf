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


if __name__=='__main__':unittest.main()
