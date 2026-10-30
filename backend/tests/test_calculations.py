from datetime import date, datetime, timezone
import math
import pytest
from app.services.calculations import complete_session, guidance_comparison, percent_change, volume_ratio

@pytest.mark.parametrize('current,previous,expected',[(1070,1000,7), (900,1000,-10),(0,100,-100),(0,0,None),(100,None,None),(None,100,None),(-50,-100,50),(50,-50,200),(float('nan'),100,None),(100,float('inf'),None)])
def test_percent_change(current,previous,expected):
    assert percent_change(current,previous)==expected

def test_volume_excludes_current_and_requires_full_history():
    assert volume_ratio(300,[100]*20,20)==3
    assert volume_ratio(300,[100]*19,20) is None
    assert volume_ratio(300,[0]*20,20) is None
    assert volume_ratio(300,[100]*19+[-1],20) is None

def test_incomplete_candle_is_excluded_until_buffer():
    day = date(2026,10,30)
    assert not complete_session(day,datetime(2026,10,30,10,0,tzinfo=timezone.utc))
    assert complete_session(day,datetime(2026,10,30,13,0,tzinfo=timezone.utc))
    assert complete_session(date(2026,10,29),datetime(2026,10,30,4,tzinfo=timezone.utc))
    assert not complete_session(date(2026,10,31),datetime(2026,10,30,13,tzinfo=timezone.utc))

def test_guidance_range_not_midpoint_and_pp_not_percent():
    assert guidance_comparison(1,3,4.2)=={'status':'exceeded','deviation_pp':1.2,'midpoint_deviation_pp':2.2}
    assert guidance_comparison(3.75,4.5,4.2)['status']=='achieved'
    assert guidance_comparison(4.5,5,4.2)['deviation_pp']==-0.3
    with pytest.raises(ValueError):
        guidance_comparison(5,4,4.2)
