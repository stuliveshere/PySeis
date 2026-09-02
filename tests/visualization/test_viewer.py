
import pytest
import numpy as np
import matplotlib.pyplot as plt
from pyseis.visualization.viewer import SeismicViewer

def test_viewer_init(synthetic_data):
    """Test viewer initialization and navigation without showing window."""
    # synthetic_data has 'fldr' column with 2 groups (from conftest update)
    
    viewer = SeismicViewer(synthetic_data, group_by='fldr', show=False)
    
    assert viewer.keys == [1, 2]
    assert len(viewer.groups) == 2
    assert viewer.current_idx == 0
    assert viewer.fig is not None
    assert viewer.ax is not None
    
    # Check initial title contains first key
    title = viewer.ax.get_title()
    assert "Gather: fldr=1" in title
    
    # Test Next
    viewer.next(None)
    assert viewer.current_idx == 1
    title = viewer.ax.get_title()
    assert "Gather: fldr=2" in title
    
    # Test Next again (should stay at last)
    viewer.next(None)
    assert viewer.current_idx == 1
    
    # Test Prev
    viewer.prev(None)
    assert viewer.current_idx == 0
    title = viewer.ax.get_title()
    assert "Gather: fldr=1" in title

def test_viewer_invalid_path():
    with pytest.raises(FileNotFoundError):
        SeismicViewer("non_existent_path.seis", show=False)

def test_viewer_bad_group_by(synthetic_data):
    with pytest.raises(ValueError, match="not found"):
        SeismicViewer(synthetic_data, group_by='invalid_header', show=False)
