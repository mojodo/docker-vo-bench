import numpy as np
import cv2
import sys
import yaml
import os.path as op

BASELINE = 0.10096822449780929


class OmniCamera:
    def __init__(self, intrin_, imgsz_, dist_, xi_):
        # intrinsics: fx, fy, cx, cy
        self.intrin = intrin_
        # image size
        self.imgsz = imgsz_
        # distortion param
        self.D = np.array(dist_, dtype=np.double)
        # omni param
        self.xi = xi_
        # stereo baseline
        # src camera matrix
        self.K = self.camera_matrix(intrin_)
        # rotation
        self.R = np.identity(3, dtype=np.double)
        # dst camera matrix
        self.P = np.array([[imgsz_[0]/3.5, 0, imgsz_[0]/2],
                          [0, imgsz_[1]/3.5, imgsz_[1]/2],
                          [0, 0, 1]], dtype=np.double)

    @staticmethod
    def camera_matrix(intrin):
        K = np.array([[intrin[0], 0, intrin[2]],
                      [0, intrin[1], intrin[3]],
                      [0, 0, 1]], dtype=np.double)
        return K

    def fx(self):
        return self.intrin[0]

    def fy(self):
        return self.intrin[1]

    def cx(self):
        return self.intrin[2]

    def cy(self):
        return self.intrin[3]

    def width(self):
        return self.imgsz[0]

    def height(self):
        return self.imgsz[1]


def tum_vi():
    cv2.ocl.setUseOpenCL(False)
    sys.path.append("/usr/local/lib/python3.5/dist-packages/cv2")
    cam0 = OmniCamera(intrin_=[533.340727445877, 533.2556495307942, 254.64689387916482, 256.4835490935692],
                      imgsz_=[512, 512],
                      dist_=[-0.05972430882700243, 0.17468739202093328, 0.000737218969875311, 0.000574074894976456],
                      xi_=1.792187901303534)
    cam1 = OmniCamera(intrin_=[520.2546241208013, 520.1799003708908, 252.24978846121377, 254.15045097300418],
                      imgsz_=[512, 512],
                      dist_=[-0.07693518083211431, 0.12590335598238764, 0.0016421936053305271, 0.0006230553630283544],
                      xi_=1.7324175606483596)
    print("cam0 opt matrix\n", cam0.P)
    print("cam1 opt matrix\n", cam1.P)

    srcyaml = "/work/ORB_SLAM2/Examples/Stereo/EuRoC.yaml"
    dstyaml = "/work/ORB_SLAM2/Examples/Stereo/TUM_VI.yaml"
    sample = "/work/scripts/calib_sample.png"
    yaml.add_constructor(u"tag:yaml.org,2002:opencv-matrix", opencv_matrix_constructor)
    yaml.add_representer(np.ndarray, opencv_matrix_representer)
    convert_yaml(cam0, cam1, srcyaml, dstyaml)

    test_undistortion(sample, cam0)


def convert_yaml(cam0, cam1, srcyaml, dstyaml):
    with open(srcyaml, 'r') as fin:
        firstline = fin.readline()
        data = yaml.load(fin)
        data["Camera.fx"] = cam0.fx()
        data["Camera.fy"] = cam0.fy()
        data["Camera.cx"] = cam0.cx()
        data["Camera.cy"] = cam0.cy()
        data["Camera.width"] = cam0.width()
        data["Camera.height"] = cam0.height()
        data["Camera.bf"] = cam0.fx() * BASELINE
        data["Omni"] = 1

        data["LEFT.width"] = cam0.width()
        data["LEFT.height"] = cam0.height()
        data["LEFT.xi"] = cam0.xi
        data["LEFT.D"] = cam0.D
        data["LEFT.K"] = cam0.K
        data["LEFT.R"] = cam0.R
        data["LEFT.P"] = cam0.P

        data["RIGHT.width"] = cam1.width()
        data["RIGHT.height"] = cam1.height()
        data["RIGHT.xi"] = cam1.xi
        data["RIGHT.D"] = cam1.D
        data["RIGHT.K"] = cam1.K
        data["RIGHT.R"] = cam1.R
        data["RIGHT.P"] = cam1.P

        with open(dstyaml, 'w') as fout:
            fout.write(firstline)
            yaml.dump(data, fout)


def test_undistortion(sample_file, cam0):
    sample = cv2.imread(sample_file)
    undist = np.zeros(tuple(cam0.imgsz))
    undist = cv2.omnidir.undistortImage(sample, cam0.K, cam0.D, np.array(cam0.xi, dtype=np.double),
                                        cv2.omnidir.RECTIFY_PERSPECTIVE, undist, cam0.P)
    undist_file = op.join(op.dirname(sample_file), "sample_undist.png")
    cv2.imwrite(undist_file, undist)


# A yaml constructor is for loading from a yaml node.
# This is taken from @misha 's answer: http://stackoverflow.com/a/15942429
def opencv_matrix_constructor(loader, node):
    mapping = loader.construct_mapping(node, deep=True)
    mat = np.array(mapping["data"])
    mat.resize(mapping["rows"], mapping["cols"])
    return mat


# A yaml representer is for dumping structs into a yaml node.
# So for an opencv_matrix type (to be compatible with c++'s FileStorage)
# we save the rows, cols, type and flattened-data
def opencv_matrix_representer(dumper, mat):
    if len(mat.shape) > 1:
        cols = int(mat.shape[1])
    else:
        cols = 1
    mapping = {'rows': int(mat.shape[0]), 'cols': cols, 'dt': 'd', 'data': mat.reshape(-1).tolist()}
    return dumper.represent_mapping(u"tag:yaml.org,2002:opencv-matrix", mapping)


if __name__ == "__main__":
    tum_vi()
