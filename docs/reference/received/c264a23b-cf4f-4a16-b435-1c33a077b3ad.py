from math import isfinite, pi, sqrt


def is_single_defect(axial_gap_mm, circumferential_gap_mm, diameter_mm, wall_mm):
    """Проверка изолированности по СТО (6.1)–(6.2) для ПАРЫ дефектов.

    Зазоры должны быть уже рассчитаны между ГРАНИЦАМИ дефектов, в мм.
    Это не просто расстояния между их центрами из Excel.
    """
    if not all(isfinite(x) for x in (axial_gap_mm, circumferential_gap_mm, diameter_mm, wall_mm)):
        raise ValueError("Все расстояния и размеры должны быть конечными числами")
    if min(axial_gap_mm, circumferential_gap_mm) < 0:
        raise ValueError("Зазоры не должны быть отрицательными")
    if diameter_mm <= wall_mm or wall_mm <= 0:
        raise ValueError("Должно выполняться: диаметр > толщина > 0")

    axial_limit = 2 * sqrt(diameter_mm * wall_mm)   # (6.1), мм
    circum_limit = pi * sqrt(diameter_mm * wall_mm)  # (6.2), мм
    return axial_gap_mm > axial_limit or circumferential_gap_mm > circum_limit


def calculate_single_defect(diameter_mm, wall_mm, tensile_mpa, length_mm,
                            depth_mm, pressure_mpa, n, k1, kh, m):
    """
    Соответствие (лист anom):
      diameter_mm = diameter                  наружный диаметр Dн, мм
      wall_mm     = tolschina_sten_tube        толщина стенки t, мм
      tensile_mpa = predel_prochnosti         предел прочности σвр, МПа
      length_mm   = osob_dlina                длина дефекта l, мм
      depth_mm    = osob_glubina              глубина дефекта d, мм
      pressure_mpa= pd (?)                    рабочее давление p, МПа
      n           = koeff_nadegn_n            надёжность по давлению
      k1          = koeff_nadegn_k1           надёжность по материалу
      kh          = koeff_nadegn_kh           надёжность по назначению
      m           = koeff_uslovii_m           коэффициент условий работы
    """
    numbers = (diameter_mm, wall_mm, tensile_mpa, length_mm, depth_mm,
               pressure_mpa, n, k1, kh, m)
    if not all(isfinite(x) for x in numbers):
        raise ValueError("Параметры должны быть конечными числами")
    if not (diameter_mm > wall_mm > 0 and tensile_mpa > 0 and length_mm > 0):
        raise ValueError("Требуется D > t > 0, σвр > 0 и l > 0")
    if not (0 <= depth_mm < wall_mm and pressure_mpa >= 0):
        raise ValueError("Требуется 0 <= глубина < толщина, давление >= 0")
    if min(n, k1, kh, m) <= 0:
        raise ValueError("Коэффициенты n, k1, kh, m должны быть > 0")

    # Шаг 1. (6.5) 
    Q = sqrt(1 + 0.31 * length_mm ** 2 / (diameter_mm * wall_mm))

    # Шаг 2. (6.4) Давление разрушения pкр одиночного дефекта, МПа.
    p_cr = (2 * wall_mm * tensile_mpa * (1 - depth_mm / wall_mm)
            / ((diameter_mm - wall_mm) * (1 - depth_mm / (wall_mm * Q))))

    # Шаг 3. (5.3) Расчётное сопротивление материала R1, МПа.
    R1 = m * tensile_mpa / (k1 * kh)

    # Шаг 4. (5.2) Поправка gamma на рабочее давление.
    gamma = 1 - n * pressure_mpa / R1
    if gamma <= 0:
        raise ValueError("Получено gamma <= 0. Проверьте исходные данные")

    # Шаг 5. (5.1) Коэффициент запаса K из СТО
    K = 0.9 * gamma * n * k1 * kh / m

    # Шаг 6. (6.6), (5.5): допустимое давление и критерий работоспособности.
    p_allow = p_cr / K
    return {
        "Q": Q,
        "p_cr_mpa": p_cr,
        "R1_mpa": R1,
        "gamma": gamma,
        "K_STO": K,
        "p_allow_mpa": p_allow,
        "passes": p_allow >= pressure_mpa,
    }


if __name__ == "__main__":
    cases = [
        # В.1 из приложения В СТО: дефект l=500, d=5.3 на трубе D=1420, t=18.7.
        ("СТО: пример В.1", dict(diameter_mm=1420, wall_mm=18.7,
         tensile_mpa=588.4, length_mm=500, depth_mm=5.3,
         pressure_mpa=7.4, n=1.1, k1=1.34, kh=1.1, m=0.9), None),
        # В.2 из СТО: та же труба, но более длинный и глубокий дефект.
        ("СТО: пример В.2", dict(diameter_mm=1420, wall_mm=18.7,
         tensile_mpa=588.4, length_mm=1000, depth_mm=6.8,
         pressure_mpa=7.4, n=1.1, k1=1.34, kh=1.1, m=0.9), None),
        # Реальная запись: anom, n_defekta=91199328, труба 1364.
        # Для демонстрации рабочее давление принято из поля pd=5.39 МПа.
        # pf=13.596 МПа хранится в БД как контроль, в формулу НЕ подставляется.
        ("Excel anom: дефект 91199328", dict(diameter_mm=530, wall_mm=7,
         tensile_mpa=510, length_mm=25, depth_mm=1,
         pressure_mpa=5.39, n=1.1, k1=1.34, kh=1.0, m=0.9), 13.596),
    ]

    for title, inputs, pf_from_excel in cases:
        r = calculate_single_defect(**inputs)
        print(f"\n{title}")
        print(f"  Q       = {r['Q']:.6f}")
        print(f"  pкр     = {r['p_cr_mpa']:.6f} МПа")
        print(f"  R1      = {r['R1_mpa']:.6f} МПа")
        print(f"  gamma   = {r['gamma']:.6f}")
        print(f"  KСТО    = {r['K_STO']:.6f}")
        print(f"  pдоп    = {r['p_allow_mpa']:.6f} МПа")
        print(f"  pраб    = {inputs['pressure_mpa']:.6f} МПа")
        print(f"  Итог    = {'КРИТЕРИЙ ВЫПОЛНЕН' if r['passes'] else 'КРИТЕРИЙ НЕ ВЫПОЛНЕН'}")
        if pf_from_excel is not None:
            print(f"  pf (БД) = {pf_from_excel:.6f} МПа; расхождение = "
                  f"{r['p_cr_mpa'] - pf_from_excel:+.6f} МПа")

