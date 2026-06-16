UPDATE parts_catalog
SET
    name = CASE sku
        WHEN 'BOILER-PROBE' THEN 'Датчик уровня бойлера'
        WHEN 'DELONGHI-THERMOBLOCK-GASKET' THEN 'Прокладка термоблока DeLonghi'
        WHEN 'E61-GASKET-73' THEN 'Прокладка группы E61 73 мм'
        WHEN 'E61-SCREEN' THEN 'Душевая сетка группы E61'
        WHEN 'JURA-BREW-SEAL-KIT' THEN 'Комплект уплотнителей заварочного узла Jura'
        WHEN 'SIMONELLI-STEAM-VALVE-SEAL' THEN 'Уплотнитель парового клапана Nuova Simonelli'
        WHEN 'SAECO-FLOW-METER' THEN 'Датчик протока Saeco'
        WHEN 'ULKA-EP5-PUMP' THEN 'Вибрационный насос Ulka EP5'
        WHEN 'GAGGIA-CLASSIC-PUMP-DIAMETER-20-MM' THEN 'Вибрационный насос Gaggia Classic 20 мм'
        WHEN 'GAGGIA-CLASSIC-GASKET-CONNECTOR-55-MM' THEN 'Уплотнитель соединения Gaggia Classic 55 мм'
        ELSE name
    END,
    compatibility_note = CASE sku
        WHEN 'BOILER-PROBE' THEN 'Универсальный датчик бойлера; перед установкой сверить резьбу и длину.'
        WHEN 'DELONGHI-THERMOBLOCK-GASKET' THEN 'Прокладка термоблока для распространенных автоматических машин DeLonghi.'
        WHEN 'E61-GASKET-73' THEN 'Подходит для распространенных групп E61; перед установкой проверить толщину.'
        WHEN 'E61-SCREEN' THEN 'Совместима с распространенными машинами на группе E61.'
        WHEN 'JURA-BREW-SEAL-KIT' THEN 'Сервисный комплект для уплотнений заварочного узла Jura серии E.'
        WHEN 'SIMONELLI-STEAM-VALVE-SEAL' THEN 'Уплотнитель парового клапана для коммерческих машин Nuova Simonelli.'
        WHEN 'SAECO-FLOW-METER' THEN 'Датчик протока для автоматических машин Saeco и Philips/Saeco.'
        WHEN 'ULKA-EP5-PUMP' THEN 'Вибрационный насос Ulka EP5; перед установкой сверить питание и крепление.'
        WHEN 'GAGGIA-CLASSIC-PUMP-DIAMETER-20-MM' THEN 'Вибрационный насос 20 мм для Gaggia Classic; перед установкой сверить крепление и питание.'
        WHEN 'GAGGIA-CLASSIC-GASKET-CONNECTOR-55-MM' THEN 'Уплотнитель соединения 55 мм для Gaggia Classic.'
        ELSE compatibility_note
    END,
    part_type = CASE sku
        WHEN 'BOILER-PROBE' THEN 'probe'
        WHEN 'DELONGHI-THERMOBLOCK-GASKET' THEN 'gasket'
        WHEN 'E61-GASKET-73' THEN 'gasket'
        WHEN 'E61-SCREEN' THEN 'screen'
        WHEN 'JURA-BREW-SEAL-KIT' THEN 'seal kit'
        WHEN 'SIMONELLI-STEAM-VALVE-SEAL' THEN 'seal'
        WHEN 'SAECO-FLOW-METER' THEN 'flow meter'
        WHEN 'ULKA-EP5-PUMP' THEN 'pump'
        WHEN 'GAGGIA-CLASSIC-PUMP-DIAMETER-20-MM' THEN 'pump'
        WHEN 'GAGGIA-CLASSIC-GASKET-CONNECTOR-55-MM' THEN 'gasket'
        ELSE part_type
    END,
    parameter_label = CASE sku
        WHEN 'BOILER-PROBE' THEN 'thread/length'
        WHEN 'DELONGHI-THERMOBLOCK-GASKET' THEN 'application'
        WHEN 'E61-GASKET-73' THEN 'diameter'
        WHEN 'E61-SCREEN' THEN 'group'
        WHEN 'JURA-BREW-SEAL-KIT' THEN 'series'
        WHEN 'SIMONELLI-STEAM-VALVE-SEAL' THEN 'application'
        WHEN 'SAECO-FLOW-METER' THEN 'connector'
        WHEN 'ULKA-EP5-PUMP' THEN 'model'
        WHEN 'GAGGIA-CLASSIC-PUMP-DIAMETER-20-MM' THEN 'diameter'
        WHEN 'GAGGIA-CLASSIC-GASKET-CONNECTOR-55-MM' THEN 'connector'
        ELSE parameter_label
    END,
    parameter_value = CASE sku
        WHEN 'BOILER-PROBE' THEN 'сверить перед установкой'
        WHEN 'DELONGHI-THERMOBLOCK-GASKET' THEN 'термоблок'
        WHEN 'E61-SCREEN' THEN 'E61'
        WHEN 'JURA-BREW-SEAL-KIT' THEN 'E'
        WHEN 'SIMONELLI-STEAM-VALVE-SEAL' THEN 'паровой клапан'
        WHEN 'SAECO-FLOW-METER' THEN 'стандартное соединение'
        WHEN 'GAGGIA-CLASSIC-PUMP-DIAMETER-20-MM' THEN '20'
        ELSE parameter_value
    END,
    parameter_unit = CASE sku
        WHEN 'BOILER-PROBE' THEN NULL
        WHEN 'GAGGIA-CLASSIC-PUMP-DIAMETER-20-MM' THEN 'mm'
        WHEN 'GAGGIA-CLASSIC-GASKET-CONNECTOR-55-MM' THEN 'mm'
        ELSE parameter_unit
    END
WHERE sku IN (
    'BOILER-PROBE',
    'DELONGHI-THERMOBLOCK-GASKET',
    'E61-GASKET-73',
    'E61-SCREEN',
    'JURA-BREW-SEAL-KIT',
    'SIMONELLI-STEAM-VALVE-SEAL',
    'SAECO-FLOW-METER',
    'ULKA-EP5-PUMP',
    'GAGGIA-CLASSIC-PUMP-DIAMETER-20-MM',
    'GAGGIA-CLASSIC-GASKET-CONNECTOR-55-MM'
);

DELETE FROM part_compatibility pc
USING parts_catalog p
WHERE pc.part_id = p.id
  AND p.sku = 'GAGGIA-CLASSIC-PUMP-DIAMETER-20-MM'
  AND pc.compatibility_level = 'series'
  AND pc.brand = 'Jura'
  AND pc.series = 'серия E';

INSERT INTO part_compatibility (part_id, compatibility_level, brand, model, note)
SELECT p.id, 'exact_model', 'Gaggia', 'Classic', 'Точная совместимость для Gaggia Classic.'
FROM parts_catalog p
WHERE p.sku = 'GAGGIA-CLASSIC-PUMP-DIAMETER-20-MM'
  AND NOT EXISTS (
      SELECT 1
      FROM part_compatibility pc
      WHERE pc.part_id = p.id
        AND pc.compatibility_level = 'exact_model'
        AND pc.brand = 'Gaggia'
        AND pc.model = 'Classic'
  );

UPDATE part_compatibility pc
SET machine_family = CASE pc.machine_family
    WHEN 'Boiler probe' THEN 'датчик бойлера'
    WHEN 'E61 group' THEN 'группа E61'
    WHEN 'Commercial steam valve' THEN 'паровой клапан коммерческой линейки'
    WHEN 'Philips/Saeco automatic' THEN 'автоматические машины Philips/Saeco'
    ELSE pc.machine_family
END;

UPDATE part_compatibility pc
SET series = CASE pc.series
    WHEN 'Automatic thermoblock' THEN 'автоматический термоблок'
    WHEN 'E series' THEN 'серия E'
    WHEN 'Commercial steam valve' THEN 'паровой клапан коммерческой линейки'
    WHEN 'Philips/Saeco automatic' THEN 'автоматические машины Philips/Saeco'
    ELSE pc.series
END;
