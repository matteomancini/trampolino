# -*- coding: utf-8 -*-
"""
Relating the workflows for force mode of trampolino

"""

def get_parent(workflow):
    
    wf_link = {
        "mrtrix_msmt_csd": None,
        "dtk_dtirecon": None,
        "dsi_rec": None,
        
        "mrtrix_tckgen": "mrtrix_msmt_csd",
        "dtk_dtitracker": "dtk_dtirecon",
        "dsi_trk": "dsi_rec",
        
        "mrtrix_tcksift": "mrtrix_tckgen",
        "dtk_spline": "dtk_dtitracker"
        }
    
    return wf_link.get(workflow)
