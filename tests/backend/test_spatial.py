import pytest
from backend.app.services.spatial_groups import sequence_candidates, merge_projection, calculate_spatial


@pytest.mark.parametrize('lengths,depths,gaps,expected,ids',[
    ([370,440],[4.3,5.9],[110],12.828630,['1','2']),
    ([50,100,150,200],[2,6,3,4],[100,200,300],14.513716,['2','3','4'])])
def test_normative_sequences(lengths,depths,gaps,expected,ids):
    items=[]
    x=0
    for i,(length,depth) in enumerate(zip(lengths,depths)):
        items.append({'start':x,'end':x+length,'depth':depth,'ids':[str(i+1)]})
        x+=length+(gaps[i] if i<len(gaps) else 0)
    best=min(sequence_candidates(items,1420,18.7,588.4),key=lambda x:x['pressureMpa'])
    assert best['pressureMpa']==pytest.approx(expected,abs=2e-6)
    assert best['memberIds']==ids


def test_ext_int_projection_depths_add():
    result=merge_projection([{'start':0,'end':10,'sides':{'EXT':2},'ids':['a']},
                            {'start':5,'end':20,'sides':{'INT':3},'ids':['b']}])
    assert result[0]['depth']==5
    assert result[0]['end']==20


def test_spatial_windows_and_cyclic_clock():
    inputs={'diameter_mm':530,'wall_mm':7,'tensile_mpa':510}
    rows=[{'n_defekta':str(i),'rasst_do_nach_osob_odom':x,'osob_dlina':100,
           'ugol_do_center_osob':angle,'osob_shirina':30,'place_on_tube':'EXT','osob_glubina':1}
          for i,x,angle in [(1,0,11.99),(2,.15,.01),(3,.6,0)]]
    result=calculate_spatial(rows,inputs)
    assert result['windowCount']>1
    assert result['lineCount']>1
    assert result['critical']['pressureMpa']>0
    assert any(set(t['critical']['memberIds'])=={'1','2'} for t in result['traces'])
