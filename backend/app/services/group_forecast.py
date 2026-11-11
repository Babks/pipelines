"""Прогноз §В.2.4–В.2.9: рост исходных дефектов и повторная схематизация.

Конвенция роста: начало осевого интервала фиксировано, длина растёт вперёд.
Это допущение явно выводится пользователю. Группа расширяется при появлении
новых взаимодействий с известными коррозиями той же трубы и прохода ВТД.
"""
from . import legacy_core as core
from .spatial_groups import calculate_spatial


def forecast_group(rows, seed_ids, inputs, years):
    future=[]
    for row in rows:
        item=dict(row)
        item['osob_dlina']=core._as_float(row.get('osob_dlina'),'osob_dlina')+4*years
        item['osob_glubina']=core._as_float(row.get('osob_glubina'),'osob_glubina')+.2*years
        future.append(item)
    chosen=set(seed_ids)
    changed=True
    while changed:
        changed=False
        for a in future:
            if core._defect_id(a) not in chosen:continue
            for b in future:
                if core._defect_id(b) in chosen:continue
                pair=core.pair_interaction(a,b,inputs['diameter_mm'],inputs['wall_mm'])
                if pair.pair_status=='undetermined':raise ValueError('Неизвестная геометрия соседа при прогнозе группы')
                if pair.pair_status=='interacting':chosen.add(core._defect_id(b));changed=True
    component=[r for r in future if core._defect_id(r) in chosen]
    if any(r['osob_glubina']>=inputs['wall_mm'] for r in component):
        return {'pressureMpa':0.,'members':sorted(chosen),'reason':'Прогнозная глубина достигла толщины стенки'}
    result=calculate_spatial(component,inputs)
    return {'pressureMpa':result['critical']['pressureMpa'],'members':sorted(chosen),'critical':result['critical']}


def group_category(rows, seed_ids, inputs, current_pressure):
    k=core._tz_safety_factor(inputs['n'],inputs['k1'],inputs['kh'],inputs['m'])
    threshold=core._danger_threshold_mpa(inputs['pressure_mpa'],k)
    seeds=[r for r in rows if core._defect_id(r) in seed_ids]
    if any(core._as_float(r['osob_glubina'],'osob_glubina')>.5*inputs['wall_mm'] for r in seeds) or current_pressure<=threshold:
        return {'category':'A','K_TZ':k,'thresholdMpa':threshold,'forecast3y':None,'tnoYears':0.}
    forecast=forecast_group(rows,seed_ids,inputs,3.)
    pressure=lambda years:forecast_group(rows,seed_ids,inputs,years)['pressureMpa']
    tno=core._solve_tno_years(pressure,threshold)
    return {'category':'A' if tno is not None and tno<.25 else 'B' if forecast['pressureMpa']<=threshold else 'C',
            'K_TZ':k,'thresholdMpa':threshold,'forecast3y':forecast,'tnoYears':tno}
