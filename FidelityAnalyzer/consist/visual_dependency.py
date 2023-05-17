from io import BytesIO
from PIL import Image
from similarities import ClipSimilarity

def consist_visual_context_by_clipsim(new_gui, api_descriptions,clip_sim):
    sim_score_tensor = clip_sim.similarity(new_gui, api_descriptions)
    sim_scores = sim_score_tensor.numpy()
    return sim_scores

def consist_visual_context(new_gui, api_descriptions):
    m = ClipSimilarity()
    sim_score_tensor = m.similarity(new_gui, api_descriptions)
    sim_scores = sim_score_tensor.numpy()[0][0]
    return sim_scores
