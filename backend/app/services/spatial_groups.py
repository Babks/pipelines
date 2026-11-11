"""Схематизация §7.1 и перебор §7.2.

Положение начала окон и первой линии является явной конвенцией реализации:
первое окно начинается у первого дефекта, первая линия — в положении 0 часов.
Дефект на границе окна включается целиком, его измеренные размеры не обрезаются.
"""
from math import ceil, pi, sqrt
from . import legacy_core as core


def sequence_candidates(items, diameter, wall, tensile):
    """Все непрерывные n..m, включая одиночные элементы, формулы 7.1–7.7."""
    candidates = []
    for n in range(len(items)):
        for m in range(n, len(items)):
            chosen = items[n:m+1]
            length = chosen[-1]['end'] - chosen[0]['start']
            depth = sum((x['end']-x['start'])*x['depth'] for x in chosen)/length
            q, pressure = core._pressure_for_geometry(diameter,wall,tensile,length,depth)
            candidates.append({'memberIds':[i for x in chosen for i in x['ids']],
                               'lengthMm':length,'effectiveDepthMm':depth,'Q':q,'pressureMpa':pressure})
    return candidates


def merge_projection(rows):
    """Общая осевая проекция; max глубины одной стороны, сумма EXT+INT."""
    merged=[]
    for row in sorted(rows,key=lambda r:r['start']):
        if merged and row['start'] <= merged[-1]['end']:
            prev=merged[-1]
            prev['end']=max(prev['end'],row['end'])
            prev['ids']+=row['ids']
            for side,depth in row['sides'].items():
                prev['sides'][side]=max(prev['sides'].get(side,0),depth)
        else:
            merged.append({**row,'ids':list(row['ids']),'sides':dict(row['sides'])})
    for row in merged:
        row['depth']=sum(row['sides'].values())
    return merged


def calculate_spatial(rows, inputs):
    d,t,s=inputs['diameter_mm'],inputs['wall_mm'],inputs['tensile_mpa']
    circumference=pi*d
    root=sqrt(d*t)
    projection_step=pi*root
    prepared=[]
    for row in rows:
        start,end=core._axial_interval_mm(row) or (None,None)
        angle=core._as_float(row.get('ugol_do_center_osob'),'ugol_do_center_osob')
        width=core._as_float(row.get('osob_shirina'),'osob_shirina')
        side=str(row.get('place_on_tube','')).upper()
        if start is None or not 0<=angle<=12 or not 0<width<circumference or side not in ('EXT','INT'):
            raise ValueError('Для группы нужны корректные координаты, ширина и сторона EXT/INT')
        depth=core._as_float(row.get('osob_glubina'),'osob_glubina')
        core._pressure_for_geometry(d,t,s,end-start,depth)
        prepared.append({'start':start,'end':end,'center':angle/12*circumference,'width':width,
                         'sides':{side:depth},'ids':[core._defect_id(row)]})
    first=min(x['start'] for x in prepared)
    last=max(x['end'] for x in prepared)
    window_length=max(5*root,max(x['end']-x['start'] for x in prepared))
    stride=window_length-2.5*root
    window_count=max(1,ceil(max(0,last-first-window_length)/stride)+1)
    line_count=ceil(circumference/projection_step)
    if window_count*line_count>100000:
        raise ValueError('Зона слишком протяжённая: требуется разделение исходного участка')
    best=None
    traces=[]
    for wi in range(window_count):
        left=first+wi*stride
        window=[x for x in prepared if x['start']<=left+window_length and x['end']>=left]
        for li in range(line_count):
            pos=li*projection_step
            projected=[]
            for x in window:
                gap=abs(x['center']-pos)
                gap=max(0,min(gap,circumference-gap)-x['width']/2)
                if gap<=projection_step: projected.append(x)
            if not projected: continue
            candidates=sequence_candidates(merge_projection(projected),d,t,s)
            critical=min(candidates,key=lambda c:c['pressureMpa'])
            trace={'window':wi+1,'line':li+1,'windowStartMm':left,'lineClock':pos/circumference*12,
                   'candidateCount':len(candidates),'critical':critical}
            traces.append(trace)
            if best is None or critical['pressureMpa']<best['critical']['pressureMpa']:best=trace
    return {'critical':best['critical'],'criticalWindow':best['window'],'criticalLine':best['line'],
            'windowLengthMm':window_length,'overlapMm':2.5*root,'projectionStepMm':projection_step,
            'windowCount':window_count,'lineCount':line_count,'traces':traces}
