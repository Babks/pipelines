import pytest
from backend.app.services.dent_rm3 import calculate_rm3


def test_small_shallow_dent():
    r=calculate_rm3(1420,18.7,100,100,10,True)
    assert r['category']=='C'
    assert r['method']=='п. 2.2.18'


@pytest.mark.parametrize('ratio,category',[(6.01,'C'),(6,'B'),(4.51,'B'),(4.5,'A')])
def test_exact_ratio_boundaries_need_rm2(ratio,category):
    r=calculate_rm3(1420,18.7,ratio*30,ratio*30,30,True)
    assert r['preliminaryCategory']==category
    assert r['steps']['strain']>0
    if category!='C':
        assert r['category'] is None
        assert r['status']=='awaiting_rm2'


def test_applicability_guards():
    with pytest.raises(ValueError,match='подтверждение'):
        calculate_rm3(530,7,80,80,10,False)
    with pytest.raises(ValueError,match='область'):
        calculate_rm3(530,7,1000,80,10,True)
    with pytest.raises(ValueError):
        calculate_rm3(530,7,float('nan'),80,10,True)


def test_arc_geometry_against_independent_atan_identity():
    # Independent circular-segment identity alpha=2*atan(w/l).
    # D=1420,t=18.7; full short side=180, depth=30 => ratio exactly 6.
    from math import atan
    r = calculate_rm3(1420, 18.7, 200, 180, 30, True)
    steps = r['steps']
    assert steps['radiusMm'] == pytest.approx(150)
    assert steps['angleRad'] == pytest.approx(2*atan(1/3))
    assert steps['halfArcMm'] == pytest.approx(96.52516631932844)
    assert steps['strain'] == pytest.approx(0.07250184799253823)
    assert r['category'] is None
    assert r['preliminaryCategory'] == 'B'


def test_long_and_short_sides_are_interchangeable():
    a = calculate_rm3(1420,18.7,200,180,30,True)
    b = calculate_rm3(1420,18.7,180,200,30,True)
    assert a == b
