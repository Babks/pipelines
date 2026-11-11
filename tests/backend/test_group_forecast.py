from backend.app.services.group_forecast import forecast_group, group_category


def test_growth_can_add_a_neighbor():
    inputs=dict(diameter_mm=530,wall_mm=7,tensile_mpa=510,pressure_mpa=5.39,n=1.1,k1=1.34,kh=1,m=.9)
    rows=[dict(n_defekta=str(i),rasst_do_nach_osob_odom=x,osob_dlina=25,
               osob_glubina=1,osob_shirina=30,ugol_do_center_osob=0,place_on_tube='EXT')
          for i,x in [(1,0),(2,.155)]]
    current=forecast_group(rows,{'1'},inputs,0)
    future=forecast_group(rows,{'1'},inputs,3)
    assert current['members']==['1']
    assert future['members']==['1','2']
    assert future['pressureMpa']<current['pressureMpa']


def test_through_wall_forecast_has_zero_capacity():
    inputs=dict(diameter_mm=530,wall_mm=7,tensile_mpa=510)
    rows=[dict(n_defekta='1',rasst_do_nach_osob_odom=0,osob_dlina=25,
               osob_glubina=6.8,osob_shirina=30,ugol_do_center_osob=0,place_on_tube='EXT')]
    assert forecast_group(rows,{'1'},inputs,2)['pressureMpa']==0
