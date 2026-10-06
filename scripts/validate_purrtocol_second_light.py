#!/usr/bin/env python3
import hashlib,json,struct
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
ASSET=ROOT/"docs/assets/purrtocol/second-light.glb"
RECEIPT=ROOT/"docs/purrtocol-3d/SECOND_LIGHT.json"
CONTRACT=ROOT/"data/purrtocol_3d_contract.json"

def parse(path):
    d=path.read_bytes();magic,ver,total=struct.unpack_from("<4sII",d,0)
    assert magic==b"glTF" and ver==2 and total==len(d)
    off=12;j=None;binchunk=b""
    while off+8<=len(d):
        n,k=struct.unpack_from("<II",d,off);off+=8;chunk=d[off:off+n];off+=n
        if k==0x4E4F534A:j=chunk
        elif k==0x004E4942:binchunk=chunk
    assert j is not None and binchunk
    return json.loads(j.rstrip(b" \t\r\n\0").decode()),binchunk

def triangles(g):
    return sum(g["accessors"][p["indices"]]["count"]//3 for n in g["nodes"] if "mesh" in n for p in g["meshes"][n["mesh"]]["primitives"])

def main():
    r=json.loads(RECEIPT.read_text());c=json.loads(CONTRACT.read_text());data=ASSET.read_bytes();g,_=parse(ASSET)
    assert r["schema"]=="purrtocol-3d-second-light-candidate/v0"
    assert r["status"]=="experimental_asset_not_canonical"
    assert r["classification"]=="implemented_visualization_not_evidence"
    assert r["canonical_asset_unchanged"] is True
    assert r["world_laws"]=={"automatic_promotion":False,"human_reaction":"UNKNOWN","technical_quality_is_not_humor":True,"visualization_is_not_evidence":True}
    assert len(data)==r["asset_bytes"] and hashlib.sha256(data).hexdigest()==r["asset_sha256"]
    x=g["asset"]["extras"];assert x["variant_id"]=="PKV-SECOND-LIGHT-CANDIDATE" and x["canonical"] is False and x["promotion"]=="none"
    names={n.get("name") for n in g["nodes"]};assert not(set(c["required_nodes"])-names)
    A={a["name"]:a for a in g["animations"]};assert set(A)==set(c["required_animations"])
    cubic=linear=channels=0
    for a in g["animations"]:
        seen=set();channels+=len(a["channels"])
        for ch in a["channels"]:
            target=(ch["target"]["node"],ch["target"]["path"]);assert target not in seen;seen.add(target)
            s=a["samplers"][ch["sampler"]];i=g["accessors"][s["input"]];o=g["accessors"][s["output"]]
            assert i["type"]=="SCALAR" and "min" in i and "max" in i
            if s["interpolation"]=="CUBICSPLINE":cubic+=1;assert o["count"]==i["count"]*3
            elif s["interpolation"]=="LINEAR":linear+=1;assert o["count"]==i["count"]
            else:raise AssertionError(s["interpolation"])
    m=r["metrics"];assert channels==m["animation_channels"] and cubic==m["cubic_spline_samplers"] and linear==m["linear_samplers"]
    assert len(g["nodes"])==m["scene_nodes"] and len(g["animations"])==m["animation_clips"] and len(g.get("textures",[]))==0
    assert triangles(g)==m["instanced_scene_triangles"]
    assert (ROOT/c["runtime_asset"]).exists() and ROOT/c["runtime_asset"]!=ASSET
    h=(ROOT/"docs/purrtocol-3d/second-light.html").read_text()
    assert "../assets/purrtocol/second-light.glb" in h and 'animation-crossfade-duration="450"' in h
    assert "serious-midnight-commercial" in h and "Human reaction: UNKNOWN" in h and "Visualization != Evidence" in h
    for name in c["required_animations"]:assert name in h
    print(json.dumps({"status":"SECOND LIGHT CANDIDATE PASS","asset_bytes":len(data),"sha256":r["asset_sha256"],"nodes":len(g["nodes"]),"animations":sorted(A),"animation_channels":channels,"cubic_spline_samplers":cubic,"instanced_scene_triangles":triangles(g),"textures":0,"canonical_first_light_unchanged":True,"human_reaction":"UNKNOWN"},indent=2))
if __name__=="__main__":main()
