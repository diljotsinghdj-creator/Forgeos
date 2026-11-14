"""Genuine 3D characters in Blender (run with Blender's Python, the `bpy` module): modelled meshes skinned to an
armature, two-bone IK legs and arms with pole targets, a face made of blend shapes (shape keys), lights, shadows, a
tracking camera with depth of field, rendered with Cycles.

Motion comes from the same controller as the 2D engine (rig2d.Character): feet are planted in world space and only
lift once the body has passed over them, the hips ride the legs' reach, and turns are real rotations of the body.

    python -m creatorforge_worker.animation.blender3d D|E out_dir      (needs `pip install bpy`)"""
from __future__ import annotations

import math
import subprocess
import sys
from pathlib import Path

import bpy  # noqa: I001 - bmesh and mathutils come with bpy
import bmesh
from mathutils import Euler, Matrix, Quaternion, Vector

from . import face as F
from . import rig2d, speech

FPS = 24


# ---- scene helpers -------------------------------------------------------------------------------------------------
def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.fps = FPS
    return sc


def material(name, color, rough=0.55, emit=0.0, sss=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value = (*color, 1.0)
    b.inputs["Roughness"].default_value = rough
    if emit:
        b.inputs["Emission Color"].default_value = (*color, 1.0)
        b.inputs["Emission Strength"].default_value = emit
    if sss:
        b.inputs["Subsurface Weight"].default_value = sss
    return m


def srgb(r, g, b):
    def c(v):
        v /= 255.0
        return v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4
    return c(r), c(g), c(b)


# ---- mesh building -------------------------------------------------------------------------------------------------
class Builder:
    """Collects parts into one mesh: each part has a material slot and a bone (vertex group, weight 1)."""

    def __init__(self):
        self.bm = bmesh.new()
        self.groups: dict[str, list[int]] = {}
        self.mats: list[str] = []
        self.parts: dict[str, range] = {}

    def _add(self, geom_verts, bone, mat, part, start=None):
        """Remembers the part's vertices themselves (bmesh renumbers vertices as parts are added; indices are only
        final once the whole mesh is built)."""
        if mat not in self.mats:
            self.mats.append(mat)
        mi = self.mats.index(mat)
        verts = list(geom_verts)
        self.groups.setdefault(bone, []).extend(verts)
        for f in {f for v in verts for f in v.link_faces}:
            f.material_index = mi
            f.smooth = True
        if part:
            self.parts[part] = verts
        return verts

    def sphere(self, center, radius, bone, mat, scale=(1, 1, 1), part=None, seg=24, rot=None):
        start = len(self.bm.verts)
        r = bmesh.ops.create_uvsphere(self.bm, u_segments=seg, v_segments=max(8, seg // 2), radius=radius)
        vs = r["verts"]
        M = Matrix.Translation(center) @ (rot.to_matrix().to_4x4() if rot else Matrix()) @ Matrix.Diagonal((*scale, 1))
        bmesh.ops.transform(self.bm, matrix=M, verts=vs)
        return self._add(vs, bone, mat, part, start)

    def capsule(self, a, b, r1, bone, mat, r2=None, seg=16):
        a, b = Vector(a), Vector(b)
        r2 = r1 if r2 is None else r2
        d = b - a
        L = d.length
        start = len(self.bm.verts)
        res = bmesh.ops.create_cone(self.bm, cap_ends=False, cap_tris=False, segments=seg, radius1=r1, radius2=r2,
                                    depth=L)
        vs = res["verts"]
        q = Vector((0, 0, 1)).rotation_difference(d.normalized())
        bmesh.ops.transform(self.bm, matrix=Matrix.Translation((a + b) / 2) @ q.to_matrix().to_4x4(), verts=vs)
        self._add(vs, bone, mat, None, start)
        self.sphere(a, r1, bone, mat, seg=seg)
        self.sphere(b, r2, bone, mat, seg=seg)

    def disc(self, pts3d, bone, mat, part=None):
        """A filled flat shape (triangle fan around its centre) from a closed loop of points."""
        start = len(self.bm.verts)
        c = sum((Vector(p) for p in pts3d), Vector()) / len(pts3d)
        vc = self.bm.verts.new(c)
        ring = [self.bm.verts.new(p) for p in pts3d]
        for i in range(len(ring)):
            self.bm.faces.new((vc, ring[i], ring[(i + 1) % len(ring)]))
        return self._add([vc] + ring, bone, mat, part, start)

    def to_object(self, name, arm, materials: dict):
        me = bpy.data.meshes.new(name)
        self.bm.verts.index_update()
        self.groups = {b: [v.index for v in vs] for b, vs in self.groups.items()}
        self.parts = {p: [v.index for v in vs] for p, vs in self.parts.items()}
        self.bm.to_mesh(me)
        ob = bpy.data.objects.new(name, me)
        bpy.context.collection.objects.link(ob)
        for m in self.mats:
            me.materials.append(materials[m])
        for bone, idx in self.groups.items():
            vg = ob.vertex_groups.new(name=bone)
            vg.add(idx, 1.0, "REPLACE")
        mod = ob.modifiers.new("Armature", "ARMATURE")
        mod.object = arm
        ob.parent = arm
        return ob


# ---- character -----------------------------------------------------------------------------------------------------
class Char3D:
    """style: "stick" (thin black limbs, big white head) or "cartoon" (clothes, skin, hair)."""

    def __init__(self, name, height=1.75, style="stick", skin=(255, 255, 255), shirt=(40, 40, 46), pants=(40, 40, 46),
                 shoes=(30, 30, 34), hair=None, hair_color=(40, 28, 20), dress=None, head_scale=1.0, lw=1.0,
                 ink=(25, 25, 30)):
        self.name, self.H, self.style = name, height, style
        H = height
        self.motion = rig2d.Character(rig2d.Look(height=H, head=head_scale), x=0.0)
        m = self.motion
        hip = m.l_thigh + m.l_shin + m.ankle
        self.hip_h = hip
        lat = 0.055 * H
        self.lat = lat
        torso = m.l_torso
        sh_h = hip + torso * 0.88
        self.sh_lat = 0.11 * H if style == "cartoon" else 0.06 * H
        hr = m.r_head
        head_c = hip + torso + m.l_neck + hr
        self.head_c = head_c
        # armature
        ad = bpy.data.armatures.new(name + "_rig")
        arm = bpy.data.objects.new(name + "_rig", ad)
        bpy.context.collection.objects.link(arm)
        bpy.context.view_layer.objects.active = arm
        bpy.ops.object.mode_set(mode="EDIT")
        eb = ad.edit_bones

        def bone(n, h, t, parent=None, deform=True, roll=0.0):
            b = eb.new(n)
            b.head, b.tail, b.roll = Vector(h), Vector(t), roll
            if parent:
                b.parent = eb[parent]
            b.use_deform = deform
            return b
        bone("root", (0, 0, 0), (0, 0, 0.15 * H), deform=False)
        bone("pelvis", (0, 0, hip - 0.04 * H), (0, 0, hip + 0.04 * H), "root")
        bone("spine", (0, 0, hip + 0.04 * H), (0, 0, hip + torso), "pelvis")
        bone("head", (0, 0, hip + torso), (0, 0, head_c + hr), "spine")
        for s, sd in (("L", 1), ("R", -1)):
            bone(f"thigh.{s}", (0, sd * lat, hip), (0.01 * H, sd * lat, hip - m.l_thigh), "pelvis")
            bone(f"shin.{s}", (0.01 * H, sd * lat, hip - m.l_thigh), (0, sd * lat, m.ankle), f"thigh.{s}")
            bone(f"foot.{s}", (0, sd * lat, m.ankle), (0.09 * H, sd * lat, m.ankle * 0.6), f"shin.{s}")
            bone(f"foot_ik.{s}", (0, sd * lat, m.ankle), (0.09 * H, sd * lat, m.ankle), None, False)
            bone(f"knee_pole.{s}", (0.8 * H, sd * lat, hip * 0.6), (0.85 * H, sd * lat, hip * 0.6), "root", False)
            bone(f"upper_arm.{s}", (0, sd * self.sh_lat, sh_h), (-0.01 * H, sd * self.sh_lat, sh_h - m.l_up), "spine")
            bone(f"forearm.{s}", (-0.01 * H, sd * self.sh_lat, sh_h - m.l_up),
                 (0, sd * self.sh_lat, sh_h - m.l_up - m.l_fore), f"upper_arm.{s}")
            bone(f"hand_ik.{s}", (0, sd * self.sh_lat, sh_h - m.l_up - m.l_fore),
                 (0, sd * self.sh_lat, sh_h - m.l_up - m.l_fore - 0.05 * H), None, False)
            bone(f"elbow_pole.{s}", (-0.8 * H, sd * self.sh_lat * 2.2, sh_h - 0.25 * H),
                 (-0.85 * H, sd * self.sh_lat * 2.2, sh_h - 0.25 * H), "root", False)
        bpy.ops.object.mode_set(mode="OBJECT")
        self.arm = arm
        for s in ("L", "R"):
            c = arm.pose.bones[f"shin.{s}"].constraints.new("IK")
            c.target, c.subtarget, c.pole_target, c.pole_subtarget = arm, f"foot_ik.{s}", arm, f"knee_pole.{s}"
            c.chain_count, c.pole_angle = 2, math.radians(-90)
            c2 = arm.pose.bones[f"foot.{s}"].constraints.new("COPY_ROTATION")
            c2.target, c2.subtarget = arm, f"foot_ik.{s}"
            c3 = arm.pose.bones[f"forearm.{s}"].constraints.new("IK")
            c3.target, c3.subtarget, c3.pole_target, c3.pole_subtarget = arm, f"hand_ik.{s}", arm, f"elbow_pole.{s}"
            c3.chain_count, c3.pole_angle = 2, math.radians(-90)
        # body mesh
        mats = {"skin": material(name + "_skin", srgb(*skin), 0.5, sss=0.05 if style == "cartoon" else 0.0),
                "ink": material(name + "_ink", srgb(*ink), 0.4), "white": material(name + "_white", (0.9, 0.9, 0.9), 0.25),
                "mouth": material(name + "_mouth", srgb(80, 18, 30), 0.6),
                "blush": material(name + "_blush", srgb(255, 120, 140), 0.6),
                "shirt": material(name + "_shirt", srgb(*shirt), 0.75), "pants": material(name + "_pants", srgb(*pants), 0.8),
                "shoes": material(name + "_shoes", srgb(*shoes), 0.4), "hair": material(name + "_hair", srgb(*hair_color), 0.5),
                "dress": material(name + "_dress", srgb(*(dress or shirt)), 0.75)}
        B = Builder()
        limb = (0.022 if style == "stick" else 0.045) * H * lw
        L = "ink" if style == "stick" else None
        for s, sd in (("L", 1), ("R", -1)):
            kx = 0.01 * H
            B.capsule((0, sd * lat, hip), (kx, sd * lat, hip - m.l_thigh), limb * (1.15 if style == "cartoon" else 1),
                      f"thigh.{s}", L or "pants")
            B.capsule((kx, sd * lat, hip - m.l_thigh), (0, sd * lat, m.ankle), limb * (0.95 if style == "cartoon" else 1),
                      f"shin.{s}", L or ("skin" if dress else "pants"), r2=limb * 0.85 if style == "cartoon" else None)
            B.sphere((0.04 * H, sd * lat, m.ankle * 0.9), 0.05 * H if style == "cartoon" else 0.03 * H, f"foot.{s}",
                     L or "shoes", scale=(1.6, 0.8, 0.55))
            B.capsule((0, sd * self.sh_lat, sh_h), (-0.01 * H, sd * self.sh_lat, sh_h - m.l_up),
                      limb * (0.85 if style == "cartoon" else 1), f"upper_arm.{s}", L or "shirt")
            B.capsule((-0.01 * H, sd * self.sh_lat, sh_h - m.l_up), (0, sd * self.sh_lat, sh_h - m.l_up - m.l_fore),
                      limb * (0.75 if style == "cartoon" else 1), f"forearm.{s}", L or "skin")
            B.sphere((0, sd * self.sh_lat, sh_h - m.l_up - m.l_fore - 0.02 * H), (0.035 if style == "cartoon" else 0.025) * H,
                     f"forearm.{s}", L or "skin")
        if style == "stick":
            B.capsule((0, 0, hip), (0, 0, hip + torso + m.l_neck), limb * 1.1, "spine", "ink")
            B.capsule((0, -self.sh_lat, sh_h), (0, self.sh_lat, sh_h), limb, "spine", "ink")
        else:
            B.sphere((0, 0, hip + 0.03 * H), 0.11 * H, "pelvis", "dress" if dress else "pants", scale=(0.75, 1.0, 0.7))
            B.capsule((0, 0, hip + 0.05 * H), (0, 0, hip + torso - 0.03 * H), 0.1 * H, "spine", "shirt", r2=0.115 * H)
            B.sphere((0, 0, sh_h), 0.12 * H, "spine", "shirt", scale=(0.7, 1.05, 0.55))
            B.capsule((0, 0, hip + torso - 0.02 * H), (0, 0, hip + torso + m.l_neck + 0.02 * H), 0.035 * H, "spine", "skin")
            if dress:
                start = len(B.bm.verts)
                res = bmesh.ops.create_cone(B.bm, cap_ends=True, segments=28, radius1=0.2 * H, radius2=0.1 * H, depth=0.3 * H)
                bmesh.ops.translate(B.bm, vec=Vector((0, 0, hip - 0.1 * H)), verts=res["verts"])
                B._add(res["verts"], "pelvis", "dress", None, start)
        # head and face (blend shapes are made below from these parts)
        B.sphere((0, 0, head_c), hr, "head", "skin" if style == "cartoon" else "white", seg=40,
                 scale=(0.95, 0.95, 1.0) if style == "cartoon" else (1, 1, 1))
        if style == "cartoon":
            B.sphere((hr * 0.97, 0, head_c - hr * 0.08), hr * 0.13, "head", "skin", scale=(1, 0.9, 1.1))   # nose
            for sd in (1, -1):
                B.sphere((0, sd * hr * 0.93, head_c - hr * 0.05), hr * 0.18, "head", "skin", scale=(0.5, 0.6, 1))
        self.hr = hr

        def on_head(u, v, out=1.012):
            """A point on the head surface: u across the face (+ = character's left), v up, facing +X."""
            x = math.sqrt(max(0.0, 1 - u * u - v * v))
            return Vector((x * hr * out, u * hr * out, head_c + v * hr * out))
        self._on_head = on_head
        for sd, nm in ((1, "L"), (-1, "R")):
            ec = on_head(sd * 0.36, 0.12, 0.95)
            B.sphere(ec, hr * 0.19, "head", "white", scale=(0.55, 1, 1.15), part=f"eye.{nm}")
            pc = on_head(sd * 0.36, 0.1, 1.05)
            B.sphere(pc, hr * 0.095, "head", "ink", scale=(0.5, 1, 1.15), part=f"pupil.{nm}")
            bc = on_head(sd * 0.36, 0.42, 1.04)
            B.sphere(bc, hr * 0.17, "head", "ink" if style == "stick" else "hair", scale=(0.3, 1, 0.22),
                     part=f"brow.{nm}")
            cc = on_head(sd * 0.55, -0.18, 1.0)
            B.sphere(cc, hr * 0.13, "head", "blush", scale=(0.25, 1, 0.6), part=f"blush.{nm}")
        self.mouth_n = 16
        B.disc([on_head(*p, 1.015) for p in _mouth_loop(0, 0, 1, 0, 0, self.mouth_n)], "head", "mouth", part="mouth")
        if hair:
            _hair(B, hair, hr, head_c)
        self.mesh = B.to_object(name, arm, mats)
        self._parts = B.parts
        self._shape_keys()
        self.arm.location = (0, 0, 0)
        self.front: list[tuple] = []
        self.cheat = 1.0

    def _shape_keys(self):
        ob, me = self.mesh, self.mesh.data
        P = self._parts
        hr, hc = self.hr, self.head_c
        full = [v.co.copy() for v in me.vertices]
        # blush hides inside the cheek at rest (the Blush key brings it out); set before any key copies the basis
        for part in ("blush.L", "blush.R"):
            idx = P[part]
            c = sum((full[i] for i in idx), Vector()) / len(idx)
            inward = (c - Vector((0, 0, hc))).normalized() * -0.06 * hr
            for i in idx:
                me.vertices[i].co = c + inward + (full[i] - c) * 0.05
        ob.shape_key_add(name="Basis", from_mix=False)
        base = [v.co.copy() for v in me.vertices]

        def key(name, fn):
            k = ob.shape_key_add(name=name, from_mix=False)
            for part, rng in P.items():
                for j, i in enumerate(rng):
                    k.data[i].co = fn(part, base[i], j, rng)
            return k
        n = self.mouth_n

        def mouth(**kw):
            loop = [self._on_head(*p, 1.015) for p in _mouth_loop(**{**dict(smile=0, open_=0, width=1, round_=0,
                                                                                   smirk=0), **kw}, n=n)]
            c = sum(loop, Vector()) / len(loop)

            def fn(part, co, j, rng):
                if part != "mouth":
                    return co
                return c if j == 0 else loop[j - 1]
            return fn
        for nm, kw in (("Smile", dict(smile=1)), ("Frown", dict(smile=-1)), ("Open", dict(open_=1)),
                       ("Wide", dict(width=1.35)), ("Narrow", dict(width=0.6)), ("Round", dict(round_=1, open_=0.6, width=0.65)),
                       ("Smirk", dict(smirk=1))):
            key("Mouth" + nm, mouth(**kw))

        def around(part, co, scale, shift=Vector()):
            rng = P[part]
            c = sum((base[i] for i in rng), Vector()) / len(rng)
            d = co - c
            return c + Vector((d.x * scale[0], d.y * scale[1], d.z * scale[2])) + shift
        eye_parts = ("eye.L", "eye.R", "pupil.L", "pupil.R")

        def eyes(scale, shift=Vector(), pupils_only=False, eyes_only=None):
            def fn(part, co, j, rng):
                if part not in eye_parts or (pupils_only and not part.startswith("pupil")):
                    return co
                side = part[-1]
                anchor = "eye." + side
                c = sum((base[i] for i in P[anchor]), Vector()) / len(P[anchor])
                d = co - c
                return c + Vector((d.x * scale[0], d.y * scale[1], d.z * scale[2])) + shift
            return fn
        key("Blink", eyes((1, 1.05, 0.06), Vector((0, 0, -0.02 * hr))))
        key("EyesWide", eyes((1.1, 1.25, 1.4)))
        key("EyesHappy", eyes((1, 1.1, 0.25), Vector((0, 0, 0.05 * hr))))
        key("LookLeft", eyes((1, 1, 1), Vector((0, 0.07 * hr, 0)), pupils_only=True))
        key("LookRight", eyes((1, 1, 1), Vector((0, -0.07 * hr, 0)), pupils_only=True))
        key("LookUp", eyes((1, 1, 1), Vector((0, 0, 0.07 * hr)), pupils_only=True))
        key("LookDown", eyes((1, 1, 1), Vector((0, 0, -0.08 * hr)), pupils_only=True))

        def brows(lift, tilt):
            def fn(part, co, j, rng):
                if not part.startswith("brow"):
                    return co
                sd = 1 if part.endswith("L") else -1
                c = sum((base[i] for i in rng), Vector()) / len(rng)
                d = co - c
                # inner end (toward the nose, -sd side) goes up with tilt>0
                inner = -sd * d.y / (0.17 * hr)
                return co + Vector((0, 0, lift * hr + tilt * inner * 0.09 * hr))
            return fn
        key("BrowUp", brows(0.14, 0))
        key("BrowDown", brows(-0.08, 0))
        key("BrowSad", brows(0, 1))
        key("BrowAngry", brows(-0.03, -1.2))

        def blush(part, co, j, rng):
            return full[rng[j]] if part.startswith("blush") else co
        key("Blush", blush)

    def set_face(self, fc: F.Face, frame: int):
        kb = self.mesh.data.shape_keys.key_blocks
        vals = {"MouthSmile": max(0, fc.smile), "MouthFrown": max(0, -fc.smile), "MouthOpen": min(1.2, fc.mouth_open),
                "MouthWide": max(0, (fc.mouth_width - 1) / 0.35), "MouthNarrow": max(0, (1 - fc.mouth_width) / 0.4),
                "MouthRound": fc.mouth_round * min(1, fc.mouth_open * 2 + 0.3), "MouthSmirk": max(0, fc.smirk),
                "Blink": max(0, 1 - min(1, fc.eye_open)) * (1 - fc.eye_smile), "EyesWide": max(0, (fc.eye_open - 1) / 0.5),
                "EyesHappy": fc.eye_smile, "LookLeft": max(0, fc.look_x), "LookRight": max(0, -fc.look_x),
                "LookUp": max(0, fc.look_y), "LookDown": max(0, -fc.look_y), "BrowUp": max(0, fc.brow_raise),
                "BrowDown": max(0, -fc.brow_raise), "BrowSad": max(0, fc.brow_tilt), "BrowAngry": max(0, -fc.brow_tilt),
                "Blush": fc.blush}
        for k, v in vals.items():
            kb[k].value = max(0.0, min(1.2, v))
            kb[k].keyframe_insert("value", frame=frame)

    def pose_frame(self, t: float, frame: int, dt: float):
        """Copies the motion controller's pose at time t into the rig and keys it."""
        m = self.motion
        m.step(t, dt)
        P = m.pose(t)
        fv = P["facing"]
        yaw = -math.acos(max(-1.0, min(1.0, fv)))           # 0 facing +X .. -pi facing -X, turning through the front
        # standing still, a character is "cheated" a little toward the camera (on -Y), as actors are on film,
        # so faces read instead of pure profiles
        still = max(0.0, 1.0 - m.speed / 0.4)
        yaw += -0.55 * (1.0 if fv >= 0 else -1.0) * still * self.cheat
        for t0, t1 in self.front:                            # turn to face the camera (on -Y) and back
            w = min(rig2d.smooth((t - t0) / 0.45), rig2d.smooth((t1 - t) / 0.45)) if t0 <= t <= t1 else 0.0
            yaw += (-math.pi / 2 - yaw) * w
        hx, hy = P["hip"]
        arm = self.arm
        arm.location = (hx, 0, 0)
        arm.rotation_euler = (0, 0, yaw)
        arm.keyframe_insert("location", frame=frame)
        arm.keyframe_insert("rotation_euler", frame=frame)
        pb = arm.pose.bones
        Rinv = Matrix.Rotation(-yaw, 4, "Z")

        def local(wx, wy, wz):
            return (Rinv @ Vector((wx - hx, wy, wz)).to_4d()).to_3d()

        def place(name, p):
            b = pb[name]
            rest = arm.data.bones[name].matrix_local
            b.matrix = Matrix.Translation(p) @ rest.to_3x3().to_4x4()
            b.keyframe_insert("location", frame=frame)
        dz = hy - self.hip_h
        pb["pelvis"].location = (0, dz, 0)
        pb["pelvis"].keyframe_insert("location", frame=frame)
        lean = P["lean"]
        # lean: rotate the spine forward around the character's side axis
        pb["spine"].rotation_mode = "QUATERNION"
        pb["spine"].rotation_quaternion = _bone_rot(arm, "spine", Vector((0, 1, 0)), lean)
        pb["spine"].keyframe_insert("rotation_quaternion", frame=frame)
        fc = P["face"]
        pb["head"].rotation_mode = "QUATERNION"
        pb["head"].rotation_quaternion = _bone_rot(arm, "head", Vector((1, 0, 0)), -math.radians(fc.head_tilt) * 0.6)
        pb["head"].keyframe_insert("rotation_quaternion", frame=frame)
        side = {0: "R", 1: "L"}                               # feet[0] is the near foot = the right foot
        f = 1.0 if fv >= 0 else -1.0
        for i, ft in enumerate(m._feet):
            s = side[i] if f > 0 else side[1 - i]
            sd = 1 if s == "L" else -1
            p = local(ft.x, sd * self.lat * (1 if yaw < math.pi / 2 else -1), ft.y + m.ankle)
            p = Vector((p.x, sd * self.lat, p.z))
            b = pb[f"foot_ik.{s}"]
            rest = arm.data.bones[f"foot_ik.{s}"].matrix_local
            b.matrix = Matrix.Translation(p) @ Matrix.Rotation(-ft.pitch * 0.6, 4, "Y") @ rest.to_3x3().to_4x4()
            b.keyframe_insert("location", frame=frame)
            b.rotation_mode = "QUATERNION"
            b.keyframe_insert("rotation_quaternion", frame=frame)
        for i, (sh, el, hd) in enumerate(P["arms"]):
            s = side[i] if f > 0 else side[1 - i]
            sd = 1 if s == "L" else -1
            p = local(hd[0], 0, hd[1])
            # a raised hand swings out to the side (a wave or a cheer clears the head instead of touching it)
            up = max(0.0, (hd[1] - sh[1]) / (m.l_up + m.l_fore))
            p = Vector((p.x * (1 - 0.4 * up), sd * self.sh_lat * (1.15 + 2.4 * up), p.z))
            place(f"hand_ik.{s}", p)
        self.set_face(fc, frame)

    def pose_actor(self, a, t: float, frame: int, dt: float):
        """Drives the rig from the keyframe stick engine (stick.Actor) instead: hips, spine, head, both feet and both
        hands go exactly where the engine solved them - jumps on real gravity, rolls, falls, body language - and the
        knee and elbow pole targets follow the solved knees and elbows, so a joint never flips through a roll."""
        a.step(t, dt)
        p = a.pose_now
        J = a.joints(p)
        f = 1.0 if p.f >= 0 else -1.0
        yaw = 0.0 if f > 0 else -math.pi
        still = 0.0 if a._act is not None else max(0.0, 1.0 - a.speed / 0.4)
        yaw += -0.55 * f * still * self.cheat
        for t0, t1 in self.front:
            w = min(rig2d.smooth((t - t0) / 0.45), rig2d.smooth((t1 - t) / 0.45)) if t0 <= t <= t1 else 0.0
            yaw += (-math.pi / 2 - yaw) * w
        hx, hy = J["hip"]
        arm = self.arm
        arm.location = (hx, (a.z_at(t) - a.z) * 8.0, 0)     # a depth step (passing someone) is a real step aside
        arm.rotation_euler = (0, 0, yaw)
        arm.keyframe_insert("location", frame=frame)
        arm.keyframe_insert("rotation_euler", frame=frame)
        pb = arm.pose.bones
        Rinv = Matrix.Rotation(-yaw, 4, "Z")

        def local(wx, wz):
            return (Rinv @ Vector((wx - hx, 0.0, wz)).to_4d()).to_3d()

        def place(name, v):
            b = pb[name]
            rest = arm.data.bones[name].matrix_local
            b.matrix = Matrix.Translation(v) @ rest.to_3x3().to_4x4()
            b.keyframe_insert("location", frame=frame)

        def pole(joint, a_end, b_end, lateral, name):
            mid = ((a_end[0] + b_end[0]) / 2, (a_end[1] + b_end[1]) / 2)
            d = (joint[0] - mid[0], joint[1] - mid[1])
            n = math.hypot(*d)
            d = (d[0] / n, d[1] / n) if n > 1e-4 else (f, 0.0)
            v = local(joint[0] + d[0] * 0.6, joint[1] + d[1] * 0.6)
            place(name, Vector((v.x, lateral, v.z)))
        pb["pelvis"].location = (0, hy - self.hip_h, 0)
        pb["pelvis"].keyframe_insert("location", frame=frame)
        pb["spine"].rotation_mode = "QUATERNION"
        pb["spine"].rotation_quaternion = _bone_rot(arm, "spine", Vector((0, 1, 0)), p.lean)
        pb["spine"].keyframe_insert("rotation_quaternion", frame=frame)
        fc = a.loco._face(t)
        pb["head"].rotation_mode = "QUATERNION"
        pb["head"].rotation_quaternion = (_bone_rot(arm, "head", Vector((0, 1, 0)), p.head * 0.8)
                                          @ _bone_rot(arm, "head", Vector((1, 0, 0)), -math.radians(fc.head_tilt) * 0.6))
        pb["head"].keyframe_insert("rotation_quaternion", frame=frame)
        side = {0: "R", 1: "L"}                               # leg/arm 0 is the near one = the right side
        for i, (hip, kn, ank, _) in enumerate(J["legs"]):
            s_ = side[i] if f > 0 else side[1 - i]
            sd = 1 if s_ == "L" else -1
            v = local(*ank)
            b = pb[f"foot_ik.{s_}"]
            rest = arm.data.bones[f"foot_ik.{s_}"].matrix_local
            b.matrix = Matrix.Translation(Vector((v.x, sd * self.lat, v.z))) @ rest.to_3x3().to_4x4()
            b.keyframe_insert("location", frame=frame)
            b.rotation_mode = "QUATERNION"
            b.keyframe_insert("rotation_quaternion", frame=frame)
            pole(kn, hip, ank, sd * self.lat, f"knee_pole.{s_}")
        for i, (sh, el, wr) in enumerate(J["arms"]):
            s_ = side[i] if f > 0 else side[1 - i]
            sd = 1 if s_ == "L" else -1
            v = local(*wr)
            up = max(0.0, (wr[1] - sh[1]) / (a.l_up + a.l_fore))     # a raised hand clears the head
            place(f"hand_ik.{s_}", Vector((v.x * (1 - 0.4 * up), sd * self.sh_lat * (1.15 + 2.4 * up), v.z)))
            pole(el, sh, wr, sd * self.sh_lat * 2.2, f"elbow_pole.{s_}")
        self.set_face(fc, frame)


def _bone_rot(arm, name, axis_world, angle):
    """A pose rotation (bone space) that turns the bone by `angle` around an armature-space axis."""
    rest = arm.data.bones[name].matrix_local.to_3x3()
    ax = (rest.inverted() @ axis_world).normalized()
    return Quaternion(ax, angle)


def _mouth_loop(smile=0.0, open_=0.0, width=1.0, round_=0.0, smirk=0.0, n=16):
    """Closed outline of the mouth on the face (u across, v up): a top lip curve and a bottom lip curve."""
    w = 0.36 * width * (1 - 0.4 * round_)
    v0 = -0.42
    pts = []
    half = n // 2
    corner_l = v0 + 0.07 * smile + 0.1 * smirk
    corner_r = v0 + 0.07 * smile
    for k in range(half + 1):                           # top lip, right corner -> left corner
        a = k / half
        u = -w + 2 * w * a
        cv = corner_r + (corner_l - corner_r) * a
        top = cv - 0.06 * smile * math.sin(math.pi * a) + 0.02 + 0.03 * open_ * math.sin(math.pi * a) * (1 - round_ * 0.3)
        pts.append((u, top))
    for k in range(1, half):                            # bottom lip, left -> right
        a = 1 - k / half
        u = -w + 2 * w * a
        cv = corner_r + (corner_l - corner_r) * a
        drop = 0.02 + 0.22 * open_ * math.sin(math.pi * a) ** (0.6 + 0.6 * (1 - round_))
        bottom = cv - 0.1 * max(0.0, smile) * math.sin(math.pi * a) - drop + 0.04 * max(0.0, -smile) * math.sin(math.pi * a)
        pts.append((u, bottom))
    return pts[:n]


def _hair(B: Builder, kind: str, hr: float, hc: float):
    if kind in ("short", "long", "bob"):
        # a cap of hair over the crown and back of the head, its front edge above the brows
        B.sphere((-hr * 0.3, 0, hc + hr * 0.3), hr * 1.05, "head", "hair", scale=(0.92, 1.03, 0.78))
    if kind == "long":
        B.sphere((-hr * 0.45, 0, hc - hr * 0.55), hr * 0.95, "head", "hair", scale=(0.7, 1.1, 1.35))
    if kind == "bob":
        B.sphere((-hr * 0.2, 0, hc - hr * 0.1), hr * 1.08, "head", "hair", scale=(0.9, 1.1, 0.95))
    if kind == "spiky":
        for k in range(9):
            a = math.pi * (0.15 + 0.7 * k / 8)
            B.sphere((-hr * 0.3 + math.cos(a) * hr * 0.2, math.cos(a + 1) * hr * 0.5, hc + hr * 0.85),
                     hr * 0.3, "head", "hair", scale=(1, 0.6, 1.3))


# ---- environment ---------------------------------------------------------------------------------------------------
def environment(kind: str = "park"):
    sc = bpy.context.scene
    world = bpy.data.worlds.new("World")
    sc.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes["Background"]
    bg.inputs["Color"].default_value = (*srgb(170, 205, 240), 1)
    bg.inputs["Strength"].default_value = 0.9
    bpy.ops.mesh.primitive_plane_add(size=120, location=(0, 0, 0))
    ground = bpy.context.object
    gm = material("ground", srgb(110, 165, 85), 0.9)
    nt = gm.node_tree
    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 3.0
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = (*srgb(92, 145, 70), 1)
    ramp.color_ramp.elements[1].color = (*srgb(132, 182, 96), 1)
    nt.links.new(noise.outputs["Fac"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], nt.nodes["Principled BSDF"].inputs["Base Color"])
    ground.data.materials.append(gm)
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 0.2, 0.005))
    path = bpy.context.object
    path.scale = (60, 1.4, 1)
    path.data.materials.append(material("path", srgb(214, 196, 160), 0.95))
    trunk = material("trunk", srgb(110, 78, 55), 0.9)
    leaves = [material(f"leaf{i}", srgb(*c), 0.8) for i, c in enumerate(((70, 135, 65), (95, 160, 75), (60, 120, 70)))]
    import random
    rng = random.Random(5)
    for k in range(16):
        x = -22 + k * 3.1 + rng.random()
        y = rng.choice((3.5, 4.8, 6.5, 8.0)) + rng.random()
        bpy.ops.mesh.primitive_cylinder_add(radius=0.12, depth=2.2, location=(x, y, 1.1))
        bpy.context.object.data.materials.append(trunk)
        for b in range(3):
            bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=3, radius=0.8 + rng.random() * 0.4,
                                                  location=(x + rng.uniform(-0.4, 0.4), y + rng.uniform(-0.3, 0.3),
                                                            2.5 + rng.random() * 0.8))
            o = bpy.context.object
            o.data.materials.append(rng.choice(leaves))
            bpy.ops.object.shade_smooth()
    wood = material("bench", srgb(150, 98, 60), 0.7)
    metal = material("metal", srgb(60, 62, 70), 0.35)
    for x in (3.0,):
        for z, dy, h in ((0.45, 1.6, 0.06), (0.75, 1.82, 0.25)):
            bpy.ops.mesh.primitive_cube_add(location=(x, dy, z))
            o = bpy.context.object
            o.scale = (0.9, 0.2 if h == 0.06 else 0.04, h / 2 if h != 0.06 else 0.03)
            o.data.materials.append(wood)
        for lx in (-0.8, 0.8):
            bpy.ops.mesh.primitive_cube_add(location=(x + lx, 1.65, 0.22))
            o = bpy.context.object
            o.scale = (0.04, 0.2, 0.22)
            o.data.materials.append(metal)
    bpy.ops.mesh.primitive_cylinder_add(radius=0.05, depth=3.2, location=(-4.5, 1.7, 1.6))
    bpy.context.object.data.materials.append(metal)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.22, location=(-4.5, 1.7, 3.25))
    bpy.context.object.data.materials.append(material("lamp", srgb(255, 236, 180), 0.2, emit=2.0))
    flowers = [material(f"fl{i}", srgb(*c), 0.6) for i, c in enumerate(((240, 90, 110), (250, 200, 70), (160, 110, 230)))]
    for k in range(60):
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.06, location=(rng.uniform(-15, 15), rng.uniform(1.2, 2.6), 0.08),
                                             segments=8, ring_count=6)
        bpy.context.object.data.materials.append(rng.choice(flowers))
    bpy.ops.object.light_add(type="SUN", location=(0, 0, 10))
    sun = bpy.context.object
    sun.data.energy = 3.2
    sun.data.angle = math.radians(3)
    sun.rotation_euler = Euler((math.radians(52), math.radians(-18), math.radians(-35)))
    bpy.ops.object.light_add(type="AREA", location=(-2, -6, 4))
    fill = bpy.context.object
    fill.data.energy = 300
    fill.data.size = 6
    fill.rotation_euler = Euler((math.radians(60), 0, 0))


def camera(keys, focus_obj=None, lens=40, fstop=4.0):
    """keys: [(frame, (x, y, z), (tx, ty, tz))] - camera position and where it looks."""
    bpy.ops.object.empty_add(location=keys[0][2])
    target = bpy.context.object
    bpy.ops.object.camera_add(location=keys[0][1])
    cam = bpy.context.object
    bpy.context.scene.camera = cam
    c = cam.constraints.new("TRACK_TO")
    c.target, c.track_axis, c.up_axis = target, "TRACK_NEGATIVE_Z", "UP_Y"
    cam.data.lens = lens
    cam.data.dof.use_dof = True
    cam.data.dof.focus_object = focus_obj or target
    cam.data.dof.aperture_fstop = fstop
    for fr, pos, look in keys:
        cam.location, target.location = pos, look
        cam.keyframe_insert("location", frame=fr)
        target.keyframe_insert("location", frame=fr)
    return cam, target


def render(out_dir: Path, name: str, frames: int, res=(960, 540), samples=20, audio: Path | None = None) -> Path:
    sc = bpy.context.scene
    sc.frame_start, sc.frame_end = 1, frames
    import os
    if os.environ.get("CF_3D_ENGINE", "eevee").lower() == "cycles":       # path-traced: best light, slow on a CPU
        sc.render.engine = "CYCLES"
        sc.cycles.device = "CPU"
        sc.cycles.samples = samples
        sc.cycles.use_denoising = True
        sc.cycles.max_bounces = 4
        sc.render.use_persistent_data = True
    else:                                                                 # real-time engine: soft shadows, AO, fast
        sc.render.engine = "BLENDER_EEVEE"
        sc.eevee.taa_render_samples = int(os.environ.get("CF_3D_TAA", "12"))
        for attr, val in (("use_shadows", True), ("use_gtao", True)):
            if hasattr(sc.eevee, attr):
                setattr(sc.eevee, attr, val)
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.film_transparent = False
    sc.render.image_settings.file_format = "PNG"
    frames_dir = out_dir / f"{name}_frames"
    frames_dir.mkdir(parents=True, exist_ok=True)
    import os
    if os.environ.get("CF_PREVIEW"):                     # a few low-resolution stills to check a scene quickly
        sc.render.resolution_x, sc.render.resolution_y = 640, 360
        sc.cycles.samples = 6
        for fr in [int(frames * k) for k in (0.08, 0.3, 0.5, 0.7, 0.9)]:
            sc.frame_set(max(1, fr))
            sc.render.filepath = str(out_dir / f"{name}_preview_{fr:04d}.png")
            bpy.ops.render.render(write_still=True)
        return out_dir
    sc.render.filepath = str(frames_dir / "f_")
    sc.render.use_overwrite = False                   # resumable: frames already on disk are skipped, and a frame
    sc.render.use_placeholder = True                  # being rendered is marked, so a crash or timeout costs nothing
    for f in frames_dir.glob("f_*.png"):              # a zero-byte placeholder is an unfinished frame: redo it
        if f.stat().st_size == 0:
            f.unlink()
    bpy.ops.render.render(animation=True)
    master = out_dir / f"{name}.mp4"
    cmd = ["ffmpeg", "-v", "error", "-y", "-framerate", str(FPS), "-i", str(frames_dir / "f_%04d.png")]
    if audio:
        cmd += ["-i", str(audio), "-c:a", "aac", "-b:a", "256k", "-shortest"]
    subprocess.run(cmd + ["-c:v", "libx264", "-preset", "slow", "-crf", "14", "-profile:v", "high", "-pix_fmt", "yuv420p",
                          "-movflags", "+faststart", str(master)], check=True)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(master), "-c:v", "libx264",
                    "-profile:v", "main", "-level", "4.0", "-crf", "21", "-pix_fmt", "yuv420p", "-c:a", "aac", "-ar", "48000",
                    "-movflags", "+faststart", str(out_dir / f"{name}_android.mp4")], check=True)
    return master


# ---- demonstration films -------------------------------------------------------------------------------------------
def _follow_cam(chars, frames, side=(2.6, -4.3, 1.45), look_z=1.05, extra=None):
    """Camera keys every 6 frames: a three-quarter view tracking the middle of the characters (eased)."""
    keys = []
    for fr in range(1, frames + 1, 6):
        t = (fr - 1) / FPS
        xs = [c.motion.hips_x(t) for c in chars]
        mx = sum(xs) / len(xs)
        o = extra(t) if extra else (0, 0, 0, 0)
        keys.append((fr, (mx + side[0] + o[0], side[1] + o[1], side[2] + o[2]), (mx + o[3], 0, look_z + o[2] * 1.4)))
    return keys


def demo_d(out_dir: Path) -> Path:
    reset()
    environment()
    s = Char3D("Stick", 1.75, "stick")
    m = s.motion
    m.x = -5.0
    m._end_x = -5.0
    m._feet = [rig2d._Foot(-5.0 + 0.085 * 1.75), rig2d._Foot(-5.0 - 0.085 * 1.75)]
    t = m.walk(0.2, -1.0, speed=1.3)
    m.express(0, "neutral")
    m.express(t - 0.3, "happy", 0.3)
    m.gesture(t, "wave", 1.6)
    s.front.append((t + 0.1, t + 6.4))
    m.express(t + 1.7, "surprised", 0.15)
    m.gesture(t + 1.7, "surprise", 1.2)
    m.express(t + 3.0, "angry", 0.25)
    m.gesture(t + 3.0, "angry", 1.2)
    m.express(t + 4.3, "sad", 0.3)
    m.express(t + 5.4, "determined", 0.3)
    t = m.run(t + 6.6, 6.0, speed=3.6)
    m.express(t - 1.0, "excited", 0.2)
    t = m.jump(t + 0.1, 0.45, forward=1.6)
    m.express(t - 0.5, "joyful", 0.2)
    m.turn(t + 0.2, -1)
    m.gesture(t + 0.5, "cheer", 1.8)
    m.express(t + 0.5, "laughing", 0.2)
    total = t + 2.6
    frames = int(total * FPS)
    for fr in range(1, frames + 1):
        s.pose_frame((fr - 1) / FPS, fr, 1 / FPS)

    def push(tt):
        # come closer for the faces, pull back for the run
        k = rig2d.smooth((tt - 4.6) / 0.8) * rig2d.smooth((9.6 - tt) / 0.8)
        return (-1.0 * k, 1.2 * k, 0.25 * k, 0)
    camera(_follow_cam([s], frames, extra=push), lens=45, fstop=3.2)
    return render(out_dir, "Demo_D_3D_stickman", frames, samples=12)


def demo_e(out_dir: Path) -> Path:
    reset()
    environment()
    work = out_dir / "work3d"
    work.mkdir(parents=True, exist_ok=True)
    dev = Char3D("Dev", 1.8, "cartoon", skin=(205, 150, 110), shirt=(60, 110, 190), pants=(50, 55, 70),
                 shoes=(90, 60, 40), hair="short", hair_color=(25, 20, 18))
    mira = Char3D("Mira", 1.66, "cartoon", skin=(236, 190, 160), shirt=(215, 80, 110), pants=(215, 80, 110),
                  shoes=(150, 40, 60), hair="long", hair_color=(70, 40, 25), dress=(215, 80, 110))
    for c, x in ((dev, -6.0), (mira, 1.2)):
        c.motion.x = c.motion._end_x = x
        c.motion._feet = [rig2d._Foot(x + 0.08 * c.H), rig2d._Foot(x - 0.08 * c.H)]
    D, M = dev.motion, mira.motion
    M.facing = -1.0
    M.turns = [(0.0, 1.0)]
    clips = []

    def say(ch, t, text, expr, gesture="talk", voice="", pitch=50, rate=155):
        end, wav = ch.say(t, text, work / f"e_{len(clips)}.wav", voice=voice, expr=expr, gesture=gesture, pitch=pitch,
                          rate=rate)
        clips.append((t, wav))
        return end
    M.express(0, "bored")
    M.gesture(0.2, "cross_arms", 3.6)
    t = D.walk(0.4, -0.4, speed=1.4)
    D.express(t - 1.2, "happy", 0.3)
    D.gesture(t - 0.8, "wave", 1.4)
    t = say(D, t, "Hi Mira! Sorry I'm late.", "embarrassed", None, "en-us+m3", 46)
    M.turn(t - 1.5, -1)
    M.express(t - 0.6, "frustrated", 0.3)
    t = say(M, t + 0.3, "Twenty minutes, Dev!", "angry", "shake_fist", "en-us+f3", 64)
    D.express(t, "nervous", 0.25)
    D.gesture(t + 0.1, "scratch_head", 1.4)
    t = say(D, t + 0.3, "The bus broke down. But I brought cookies!", "nervous", "explain", "en-us+m3", 48)
    M.express(t, "surprised", 0.15)
    t = say(M, t + 0.4, "Cookies? Chocolate ones?", "curious", "talk", "en-us+f3", 68)
    D.nod(t, 0.9)
    D.express(t, "proud", 0.3)
    M.express(t + 0.6, "joyful", 0.25)
    M.gesture(t + 0.6, "clap", 1.6)
    t = say(M, t + 0.8, "Then you are forgiven!", "joyful", None, "en-us+f3", 70, 165)
    for c in (D, M):
        c.express(t, "laughing", 0.2)
        c.gesture(t, "laugh", 1.8)
    e1, w1 = D.say(t + 0.1, "Ha ha ha!", work / "e_l1.wav", voice="en-us+m3", gesture=None, rate=200, pitch=52)
    e2, w2 = M.say(t + 0.2, "Ha ha ha ha!", work / "e_l2.wav", voice="en-us+f3", gesture=None, rate=210, pitch=72)
    clips += [(t + 0.1, w1), (t + 0.2, w2)]
    t += 2.0
    D.express(t, "happy", 0.3)
    M.express(t, "happy", 0.3)
    D.walk(t + 0.2, 6.0, speed=1.3)
    end = M.walk(t + 0.4, 6.8, speed=1.3)
    total = end - 1.0
    frames = int(total * FPS)
    for fr in range(1, frames + 1):
        for c in (dev, mira):
            c.pose_frame((fr - 1) / FPS, fr, 1 / FPS)

    def push(tt):
        k = rig2d.smooth((tt - 3.6) / 0.8) * rig2d.smooth((total - 3.2 - tt) / 0.8)
        return (-0.6 * k, 1.4 * k, 0.1 * k, 0)
    camera(_follow_cam([dev, mira], frames, side=(1.0, -5.2, 1.5), look_z=1.15, extra=push), lens=40, fstop=4.0)
    audio = speech.mix(clips, total, work / "e_mix.wav")
    return render(out_dir, "Demo_E_3D_cartoon_story", frames, samples=12, audio=audio)


def demo_5(out_dir: Path) -> Path:
    """Cinematic 3D stickman: a dejected walk, a spark of an idea, a sprint, a jump over a crate, a trip and a roll,
    embarrassment, a laugh, then standing tall - one continuous camera that tracks low, pushes in for the face,
    goes wide for the action and drops to the ground for the fall. 2.35:1 with shallow depth of field."""
    from . import motions as MO
    from .stick import Actor
    reset()
    environment()
    s = Char3D("Stick", 1.75, "stick")
    a = Actor(rig2d.Look(height=1.75), x=-6.0, seed=4)
    L = a.loco
    crate_x = 0.0
    bpy.ops.mesh.primitive_cube_add(location=(crate_x, 0.0, 0.22))
    crate = bpy.context.object
    crate.scale = (0.25, 0.3, 0.22)
    crate.data.materials.append(material("crate", srgb(196, 140, 72), 0.7))
    bpy.ops.object.shade_smooth()
    # the performance
    L.express(0, "sad", 0.3)
    t = a.walk(0.3, -2.6, 0.9)
    a.posture(0.3, t + 0.2, lean=0.22, crouch=0.02)          # shoulders down, head down: a bad day
    a.feel(t, t + 1.7, "sad")
    t1 = t + 1.7
    L.express(t1, "surprised", 0.12)
    a.feel(t1, t1 + 0.9, "surprised")
    s.front.append((t1 - 0.15, t1 + 2.5))
    L.express(t1 + 0.9, "excited", 0.2)
    a.feel(t1 + 0.9, t1 + 2.4, "excited")
    t_run = t1 + 2.7
    t = a.run(t_run, crate_x - 0.95, 4.0)
    L.express(t_run, "determined", 0.2)
    t = MO.jump(a, t - 0.05, dist=1.9, height=0.55)
    L.express(t - 0.7, "joyful", 0.2)
    t = a.run(t, 4.4, 4.0)
    t_roll = t - 0.12
    L.express(t_roll + 0.05, "surprised", 0.1)
    t = MO.trip_roll(a, t_roll)
    L.express(t - 0.3, "embarrassed", 0.25)
    a.feel(t, t + 1.1, "embarrassed")
    L.express(t + 1.1, "laughing", 0.2)
    a.feel(t + 1.1, t + 2.5, "laugh")
    s.front.append((t + 0.5, t + 6.0))
    L.express(t + 2.5, "proud", 0.3)
    a.feel(t + 2.5, t + 3.9, "confident")
    t_end_roll = t
    total = t + 4.1
    frames = int(total * FPS)
    hips = []
    for fr in range(1, frames + 1):
        s.pose_actor(a, (fr - 1) / FPS, fr, 1 / FPS)
        hips.append(a.hip)
    # one continuous camera: shot "looks" blended in time, following a smoothed hip track
    shots = [(0.0, (2.0, -3.4, 0.42), (0.35, 1.2), 30),              # low tracking: the walk
             (t1 - 0.8, (0.35, -2.25, 1.5), (0.0, 1.48), 58),       # push in: the face
             (t_run + 0.2, (1.6, -6.2, 1.05), (1.1, 0.95), 28),     # wide, leading: sprint and jump
             (t_roll - 0.5, (1.0, -2.9, 0.32), (0.7, 0.55), 26),    # down on the ground: the fall
             (t_end_roll + 0.5, (-0.5, -2.7, 1.3), (0.0, 1.3), 48),  # medium: embarrassed, laughing
             (total - 1.2, (-0.15, -2.05, 1.45), (0.0, 1.42), 62)]  # slow push-in: standing tall

    def blend(tt):                                             # each shot eases in over the 1.2 s before it starts
        _, pos, look, ln = shots[0]
        for tb, pb_, lb, fb in shots[1:]:
            k = rig2d.smooth(min(1.0, max(0.0, (tt - (tb - 1.2)) / 1.2)))
            pos = tuple(x + (y - x) * k for x, y in zip(pos, pb_))
            look = tuple(x + (y - x) * k for x, y in zip(look, lb))
            ln = ln + (fb - ln) * k
        return pos, look, ln
    xs = [h[0] for h in hips]
    sm = []
    for i in range(len(xs)):                                   # a camera operator's lag, not a lock-on
        w = xs[max(0, i - 8): i + 9]
        sm.append(sum(w) / len(w))
    keys, lens = [], []
    for fr in range(1, frames + 1, 3):
        pos, look, ln = blend((fr - 1) / FPS)
        mx = sm[fr - 1]
        keys.append((fr, (mx + pos[0], pos[1], pos[2]), (mx + look[0], 0.0, look[1])))
        lens.append((fr, ln))
    cam, _ = camera(keys, lens=lens[0][1], fstop=2.2)
    for fr, ln in lens:
        cam.data.lens = ln
        cam.data.keyframe_insert("lens", frame=fr)
    return render(out_dir, "Demo5_cinematic_3D_stickman", frames, res=(1280, 544), samples=12)


def _blocks(world, depth=(-0.9, 0.9), color=(150, 150, 158), name="stairs"):
    """Solid 3D geometry for a stick-engine World's platforms (stairs, ledges), so feet land on real steps."""
    mat = material(name, srgb(*color), 0.8)
    for x0, x1, top in world.platforms:
        bpy.ops.mesh.primitive_cube_add(location=((x0 + x1) / 2, (depth[0] + depth[1]) / 2, top / 2))
        o = bpy.context.object
        o.scale = ((x1 - x0) / 2, (depth[1] - depth[0]) / 2, top / 2)
        o.data.materials.append(mat)


def demo_f(out_dir: Path) -> Path:
    """Stress test F: three rigged 3D stickmen moving through a 3D park - stairs up and down, a sprint and a vault over
    a crate, sitting on a bench, reacting to each other - driven by the stick engine, filmed by a continuous camera."""
    reset()
    environment()
    from .stress import testf_checked
    actors, w, total, before, after, fixes = testf_checked(FPS)
    print("Test F QC before:", before.summary(), "| corrections:", fixes, "| after:", after.summary())
    _blocks(w)
    from .stress import BENCH_X, CRATE_X
    bpy.ops.mesh.primitive_cube_add(location=(CRATE_X, 0.0, 0.22))   # the crate
    crate = bpy.context.object
    crate.scale = (0.24, 0.3, 0.22)
    crate.data.materials.append(material("crate", srgb(196, 140, 72), 0.7))
    wood = material("bench2", srgb(150, 98, 60), 0.7)
    for z, sx, sz, dx in ((0.43, 0.55, 0.03, 0.0), (0.2, 0.03, 0.2, -0.45), (0.2, 0.03, 0.2, 0.45)):
        bpy.ops.mesh.primitive_cube_add(location=(BENCH_X + dx, 0.0, z))
        o = bpy.context.object
        o.scale = (sx, 0.22, sz)
        o.data.materials.append(wood)
    inks = {"Ash": (40, 90, 200), "Ivy": (200, 60, 70), "Kit": (40, 150, 80)}
    chars = [Char3D(a.look.name, 1.75, "stick", ink=inks[a.look.name]) for a in actors]
    t_k = max(x.t1 for x in actors[2].acts)
    t = actors[0].loco.moves[0][1]
    frames = int(total * FPS)
    hips = []
    for fr in range(1, frames + 1):
        tt = (fr - 1) / FPS
        for c, a in zip(chars, actors):
            c.pose_actor(a, tt, fr, 1 / FPS)
        hips.append([a.hip for a in actors])
    # camera: crane down over the stairs following Ash, swing round as Kit sprints and vaults, settle on the group
    keys = []
    for fr in range(1, frames + 1, 3):
        tt = (fr - 1) / FPS
        hx = [h[0] for h in hips[fr - 1]]
        k = rig2d.smooth((tt - (t - 3.4)) / 2.0)                       # from Ash to the action at the crate
        mx = hx[0] * (1 - k) + (hx[2] * 0.6 + 6.5 * 0.4) * k
        height = 3.2 - 1.6 * rig2d.smooth(tt / 4.0) + 0.3 * k
        keys.append((fr, (mx + 1.6 - 1.0 * k, -5.4 + 0.6 * k, height), (mx + 0.4, 0.0, 1.0 + 0.2 * (1 - k))))
    camera(keys, lens=32, fstop=4.5)
    return render(out_dir, "TestF_3D_environment", frames, res=(1280, 544), samples=12)


def asset_mesh(asset: dict, x: float, y: float, depth: float | None = None, name: str = ""):
    """A library asset as Blender objects: every part extruded into a closed prism (checked by asset_lib.to_mesh:
    no open edges) with its own colour, standing at (x, y) in the scene."""
    from . import asset_lib
    objs = []
    for k, part in enumerate(sorted(asset["parts"], key=lambda p: p.get("z", 0))):
        m = asset_lib.to_mesh({**asset, "parts": [part]}, depth)
        if m["open_edges"]:
            raise ValueError(f"{name or asset['name']}: part {part['id']} is not a closed mesh")
        me = bpy.data.meshes.new(f"{name}_{part['id']}")
        me.from_pydata([(vx, vy - 0.002 * k, vz) for vx, vy, vz in m["verts"]], [], m["faces"])
        me.update()
        ob = bpy.data.objects.new(me.name, me)
        bpy.context.collection.objects.link(ob)
        ob.location = (x, y, 0.0)
        ob.data.materials.append(material(me.name, srgb(*part["fill"]), 0.6))
        objs.append(ob)
    return objs


def _dusk(frames: int, lamps: list):
    """Dynamic lighting over the shot: the sun sinks and warms toward sunset, the sky dims, and the lamp posts
    switch on and glow brighter as the light goes (keyframed: sun angle, energy and colour, sky colour and
    strength, lamp light energy)."""
    sun = next(o for o in bpy.data.objects if o.type == "LIGHT" and o.data.type == "SUN")
    bg = bpy.context.scene.world.node_tree.nodes["Background"]
    pts = []
    for x, y, z in lamps:
        bpy.ops.object.light_add(type="POINT", location=(x, y, z))
        p = bpy.context.object
        p.data.color = (1.0, 0.78, 0.45)
        p.data.shadow_soft_size = 0.25
        pts.append(p)
    for fr, k in ((1, 0.0), (int(frames * 0.45), 0.45), (frames, 1.0)):
        sun.rotation_euler = Euler((math.radians(52 + 28 * k), math.radians(-18), math.radians(-35 - 30 * k)))
        sun.data.energy = 3.2 * (1 - 0.72 * k)
        sun.data.color = (1.0, 1.0 - 0.32 * k, 1.0 - 0.6 * k)
        sun.keyframe_insert("rotation_euler", frame=fr)
        sun.data.keyframe_insert("energy", frame=fr)
        sun.data.keyframe_insert("color", frame=fr)
        top = srgb(170, 205, 240)
        dusk = srgb(240, 150, 110)
        bg.inputs["Color"].default_value = (*(a + (b - a) * k for a, b in zip(top, dusk)), 1)
        bg.inputs["Strength"].default_value = 0.9 - 0.55 * k
        bg.inputs["Color"].keyframe_insert("default_value", frame=fr)
        bg.inputs["Strength"].keyframe_insert("default_value", frame=fr)
        for p in pts:
            p.data.energy = 0.0 if k < 0.3 else 140.0 * (k - 0.3) / 0.7
            p.data.keyframe_insert("energy", frame=fr)


def demo_g(out_dir: Path, dusk: bool = False, name: str = "Benchmark_3D_multi_character") -> Path:
    """Acceptance benchmark: four characters in a 3D park (bench3d): a game of catch with a real projectile, a
    long throw that bounces away, a passer-by who returns it, a spectator on a bench - with generated library assets
    (a car and lamp posts) extruded into closed meshes for the set."""
    from . import asset_lib, bench3d
    reset()
    environment()
    actors, props, w, total, before, after, fixes = bench3d.checked(FPS)
    print("benchmark 3D QC before:", before.summary(), "| corrections:", fixes, "| after:", after.summary())
    lib = asset_lib.Library.default()
    for desc, x, y in (("a red car", 1.5, 4.2), ("lamp", -3.8, 2.2), ("lamp", 6.0, 2.2)):
        aid, how = lib.obtain(desc)
        asset_mesh(lib.get(aid), x, y, name=f"{desc.replace(' ', '_')}_{x}")
        print("set dressing:", desc, "->", aid, f"({how})")
    wood = material("bench3", srgb(150, 98, 60), 0.7)
    for z, sx, sz, dx in ((0.43, 0.55, 0.03, 0.0), (0.2, 0.03, 0.2, -0.45), (0.2, 0.03, 0.2, 0.45)):
        bpy.ops.mesh.primitive_cube_add(location=(bench3d.BENCH_X + dx, 0.0, z))
        o = bpy.context.object
        o.scale = (sx, 0.22, sz)
        o.data.materials.append(wood)
    ball = props[0]
    bpy.ops.mesh.primitive_uv_sphere_add(radius=ball.w / 2, location=(ball.x, 0.0, ball.h / 2))
    bobj = bpy.context.object
    bobj.data.materials.append(material("ball", srgb(*ball.color), 0.4))
    inks = {"Ash": (40, 90, 200), "Ivy": (200, 60, 70), "Kit": (40, 150, 80), "Mo": (230, 140, 30)}
    chars = [Char3D(a.look.name, a.look.height, "stick", ink=inks[a.look.name]) for a in actors]
    frames = int(total * FPS)
    hips = []
    for fr in range(1, frames + 1):
        tt = (fr - 1) / FPS
        for c, a in zip(chars, actors):
            c.pose_actor(a, tt, fr, 1 / FPS)
        bx, by, ang = ball.pos(tt)
        bobj.location = (bx, 0.0, by + ball.h / 2)
        bobj.rotation_euler = (0.0, -ang, 0.0)
        bobj.keyframe_insert("location", frame=fr)
        bobj.keyframe_insert("rotation_euler", frame=fr)
        hips.append([a.hip[0] for a in actors] + [bx])
    keys = []
    for fr in range(1, frames + 1, 3):                 # eye level, following the play: the two players and the ball,
        ash_x, ivy_x, kit_x, mo_x, bx = hips[fr - 1]   # and Mo once the ball reaches him; never a far-off wide shot
        core = [ash_x, ivy_x, bx]
        if abs(mo_x - bx) < 4.5:
            core.append(mo_x)
        if max(core) - min(core) > 9.0:                # too wide for the lens: follow where the ball is going
            core = [x for x in core if abs(x - bx) < 7.5] or [bx]
        lo, hi = min(core), max(core)
        mx = (lo + hi) / 2
        dist = max(6.0, min(10.0, 4.8 + 0.62 * (hi - lo)))
        keys.append((fr, (mx + 0.9, -dist, 1.4), (mx, 0.0, 1.15)))
    sm = []                                            # ease the camera: a running average of the keys (~2 s)
    for i in range(len(keys)):
        win = keys[max(0, i - 5):i + 6]
        pos = tuple(sum(k[1][j] for k in win) / len(win) for j in range(3))
        look = tuple(sum(k[2][j] for k in win) / len(win) for j in range(3))
        sm.append((keys[i][0], pos, look))
    camera(sm, lens=32, fstop=5.6)
    if dusk:
        _dusk(frames, [(-3.8, 1.95, 3.45), (6.0, 1.95, 3.45)])   # just under the lamp heads
    return render(out_dir, name, frames, res=(960, 408), samples=4)


SHOT = {   # kind -> (distance, camera height, look height, lens)
    "establish": (12.0, 3.0, 1.0, 30), "two": (6.5, 1.55, 1.1, 34), "follow": (8.0, 1.6, 1.2, 32),
    "medium": (4.6, 1.45, 1.15, 40), "action": (7.0, 1.25, 1.2, 32), "low": (6.2, 0.55, 2.0, 30),
    "group": (7.5, 1.7, 1.0, 34), "wide": (13.0, 3.2, 1.2, 28)}


def demo_c(out_dir: Path) -> Path:
    """Film C, "The Ball on the Wall": a 90-second 3D story staged on the stick engine (bench3d.film_c, QC-checked)
    and filmed from a shot list - hard cuts between shots, eased framing within a shot - at dusk."""
    from . import asset_lib, bench3d
    reset()
    environment()
    actors, props, w, total, before, after, fixes, marks = bench3d.film_c_checked(FPS)
    print("Film C QC before:", before.summary(), "| corrections:", fixes, "| after:", after.summary())
    lib = asset_lib.Library.default()
    for desc, x, y in (("a red car", -1.0, 5.0), ("lamp", 1.5, 2.2), ("lamp", 9.5, 2.2), ("lamp", bench3d.LAMP_X, 0.32),
                       ("tree", 12.0, 4.5)):
        aid, how = lib.obtain(desc)
        asset_mesh(lib.get(aid), x, y, name=f"{desc.replace(' ', '_')}_{x}")
    x0, x1, top = bench3d.WALL                       # the garden wall
    bpy.ops.mesh.primitive_cube_add(location=((x0 + x1) / 2, 0.0, top / 2))
    wall = bpy.context.object
    wall.scale = ((x1 - x0) / 2, 0.55, top / 2)
    wall.data.materials.append(material("wall", srgb(176, 120, 96), 0.85))
    wood = material("bench_c", srgb(150, 98, 60), 0.7)
    for z, sx, sz, dx in ((0.43, 0.55, 0.03, 0.0), (0.2, 0.03, 0.2, -0.45), (0.2, 0.03, 0.2, 0.45)):
        bpy.ops.mesh.primitive_cube_add(location=(bench3d.BENCH_X + dx, 0.0, z))
        o = bpy.context.object
        o.scale = (sx, 0.22, sz)
        o.data.materials.append(wood)
    ball, crate = props
    bpy.ops.mesh.primitive_uv_sphere_add(radius=ball.w / 2, location=(ball.x, 0.0, ball.h / 2))
    bobj = bpy.context.object
    bobj.data.materials.append(material("ball_c", srgb(*ball.color), 0.4))
    bpy.ops.mesh.primitive_cube_add(location=(crate.x, 0.0, crate.h / 2))
    cobj = bpy.context.object
    cobj.scale = (crate.w / 2, 0.3, crate.h / 2)
    cobj.data.materials.append(material("crate_c", srgb(*crate.color), 0.75))
    inks = {"Ash": (40, 90, 200), "Ivy": (200, 60, 70), "Kit": (40, 150, 80), "Mo": (230, 140, 30)}
    chars = [Char3D(a.look.name, a.look.height, "stick", ink=inks[a.look.name]) for a in actors]
    frames = int(total * FPS)
    pos = []
    for fr in range(1, frames + 1):
        tt = (fr - 1) / FPS
        for c, a in zip(chars, actors):
            c.pose_actor(a, tt, fr, 1 / FPS)
        bx, by, ang = ball.pos(tt)
        bobj.location = (bx, 0.0, by + ball.h / 2)
        bobj.rotation_euler = (0.0, -ang, 0.0)
        bobj.keyframe_insert("location", frame=fr)
        bobj.keyframe_insert("rotation_euler", frame=fr)
        cx, cy, _ = crate.pos(tt)
        cobj.location = (cx, 0.0, cy + crate.h / 2)
        cobj.keyframe_insert("location", frame=fr)
        pos.append({a.look.name: (a.hip[0], a.hip[1]) for a in actors} | {"ball": (bx, by)})
    # the shot list: each shot frames its subjects; within a shot the camera eases, between shots it cuts
    keys = []
    shots = sorted(marks["shots"])
    for fr in range(1, frames + 1):
        tt = (fr - 1) / FPS
        shot = next((s for s in shots if s[0] <= tt < s[1]), shots[-1])
        dist, h, look_z, _lens = SHOT[shot[2]]
        xs = [pos[fr - 1][n][0] for n in shot[3] if n in pos[fr - 1]]
        span = max(xs) - min(xs)
        mx = (max(xs) + min(xs)) / 2
        if shot[2] == "low":
            look_z = bench3d.WALL[2] + 0.8
        d = max(dist, 2.4 + 0.75 * span)
        keys.append([fr, (mx + 0.9, -d, h), (mx, 0.0, look_z), shots.index(shot)])
    sm = []
    for i, k in enumerate(keys):                      # ease within a shot only - never across a cut
        win = [q for q in keys[max(0, i - 10):i + 11] if q[3] == k[3]]
        p_ = tuple(sum(q[1][j] for q in win) / len(win) for j in range(3))
        l_ = tuple(sum(q[2][j] for q in win) / len(win) for j in range(3))
        sm.append((k[0], p_, l_))
    camera(sm, lens=32, fstop=5.6)                    # keyed on every frame: cuts are cuts
    _dusk(frames, [(1.5, 1.95, 3.45), (9.5, 1.95, 3.45), (bench3d.LAMP_X, 0.12, 3.45)])
    return render(out_dir, "FilmC_ball_on_the_wall", frames, res=(960, 408), samples=4)


if __name__ == "__main__":
    which = (sys.argv[1] if len(sys.argv) > 1 else "D").upper()
    out = Path(sys.argv[2] if len(sys.argv) > 2 else ".").resolve()
    out.mkdir(parents=True, exist_ok=True)
    test4 = lambda o: demo_g(o, dusk=True, name="Test4_cinematic_3D")   # noqa: E731
    print({"D": demo_d, "E": demo_e, "5": demo_5, "F": demo_f, "G": demo_g, "H": test4, "C": demo_c}[which](out))
