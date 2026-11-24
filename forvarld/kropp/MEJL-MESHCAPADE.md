Till: Meshcapade (licensing / sales)
Ämne: Commercial licence enquiry: SMPL and AMASS-trained motion models for a semantic video-editing tool (pre-revenue)

Hi Meshcapade team,

I'm building a tool that lets content managers edit short-form social video with plain language, and I'd like to talk about a commercial licence for SMPL and for motion models trained on AMASS.

**What we're building**
We take short videos (mostly TikTok-style clips for restaurants, cafés and shops) and break each one down into a lightweight, rigged 3D scene: the room, furniture, props, camera, and every person's body motion, recovered from the video and placed in the scene. Alongside the geometry we store what the scene means: who does what, with which hand, to whom, and what may be changed.

The result is a library of content where each clip is a template that can be edited semantically. A content manager writes something like "let her hand the sample over with her other hand", "skip the part where she scoops" or "keep the camera still". A fast decision layer picks the matching change from the options the scene allows, and the 3D scene updates in seconds. Positions, timing, props, camera and body motion can all change, and the edited scene is then rendered back into a clip.

**Where SMPL / AMASS come in**
Edits that change how a person moves (switching hands, turning towards someone, stepping closer) need a motion model that understands human movement, not just geometry. We are prototyping with physics-based motion controllers from the research community (NVIDIA's ProtoMotions / MaskedMimic), which use the SMPL body and checkpoints trained on AMASS. For now this is internal research only. To build it into the product we need a commercial path for:
1. the SMPL (and possibly SMPL-X) body model
2. using models trained on AMASS, or training our own motion models on AMASS together with our own data
3. any Meshcapade motion or avatar services that could replace or support parts of this, if they fit better

**Where we are**
The project is pre-revenue. It has been a hobby project for about a year, and we now have a working pipeline from video to a rigged, editable scene on our test clips. We clearly intend to take it to market. Volumes are small for now: a few hundred to a few thousand clips processed internally, and edits made by a small number of users.

Could you tell us which licence options you offer for this kind of use, roughly what they cost, and whether there's a startup or early-stage arrangement? I'm happy to share more detail or a short demo.

Best regards,
[name]
[company / project name]
[contact]
