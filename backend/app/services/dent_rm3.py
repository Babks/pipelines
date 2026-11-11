"""Малая вмятина: пп. 2.2.17–2.2.20 предоставленной методики.

Все размеры в мм, epsilon безразмерна. Отсутствие вторичных повреждений должно
подтверждаться исходными данными, а не подразумеваться из пустой ячейки программы.
Категории A/B по РМ3 не становятся окончательными: справка требует расчёта РМ2.
"""
from math import asin, isfinite, sqrt


def calculate_rm3(diameter_mm, wall_mm, length_mm, width_mm, depth_mm,
                  secondary_damage_absent: bool):
    values=(diameter_mm,wall_mm,length_mm,width_mm,depth_mm)
    if any(isinstance(v,bool) or not isinstance(v,(int,float)) or not isfinite(v) for v in values):
        raise ValueError('Размеры должны быть конечными числами')
    if min(values)<=0 or diameter_mm<=2*wall_mm:
        raise ValueError('Требуются положительные размеры и D > 2t')
    if secondary_damage_absent is not True:
        raise ValueError('Для РМ3 требуется подтверждение отсутствия вторичных повреждений')
    # R=D/2 принят в геометрии трубы; h в критерии малости — толщина стенки.
    root=sqrt(diameter_mm/2*wall_mm)
    if max(length_mm,width_mm)>2.5*root:
        raise ValueError('Размеры превышают область малых вмятин: требуется РМ1/РМ2')
    if max(length_mm,width_mm)<=1.25*root and depth_mm<=wall_mm:
        return {'model':'РМ3','status':'provisional','category':'C',
                'preliminaryCategory':'C','method':'п. 2.2.18',
                'steps':{'smallLimitMm':2.5*root,'noCalculationLimitMm':1.25*root}}
    half=min(length_mm,width_mm)/2
    if depth_mm>half:
        raise ValueError('Глубина превышает полудлину короткой стороны: неоднозначная ветвь дуги, нужна экспертная оценка')
    radius=(half*half+depth_mm*depth_mm)/(2*depth_mm)  # (2.5)
    angle=asin(min(1.,2*half*depth_mm/(half*half+depth_mm*depth_mm)))  # (2.7)
    arc=radius*angle  # (2.6)
    strain=(arc-half)/half  # (2.4)
    ratio=min(length_mm,width_mm)/depth_mm
    category='C' if ratio>6 else 'B' if ratio>4.5 else 'A'
    return {'model':'РМ3','status':'provisional' if category=='C' else 'awaiting_rm2',
            'category':'C' if category=='C' else None,'preliminaryCategory':category,
            'method':'пп. 2.2.19–2.2.20; справка о финальной оценке по РМ2',
            'steps':{'halfShortSideMm':half,'radiusMm':radius,'angleRad':angle,
                     'halfArcMm':arc,'strain':strain,'sizeDepthRatio':ratio,'smallLimitMm':2.5*root}}
