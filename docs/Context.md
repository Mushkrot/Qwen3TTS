

9h
3h
36m

Пройдись по всей директории AI просмотри проекты. Несколько из низ свфзаны с попыткой сожлать систему генерации голоса, похожего на голос оригинала. То есть была поптыка найчить какую-то из моделей совему голосу на собственном dataset. Задача была науцчить очень похоже, то есть на 0-shot. Много моделей на рунке, которые по 3-10 секунд завука дают некое подобие голоса, но они дают голос не очень походий. Илея была нацучить именно н абольшом dataset, чтобы голос был очень правдаподобным.

Однако мы столкнудиьс вот стакими проблемами:
-- Голос оригинала на русском языке. Некоторые модели не умеют хорошо работать с русским оришгиналом. ПРи этом голос которыцй мы будем генерировать - на английском. Я понимабю, что будет акцент, но это не страшно. Акуент приемелем. Важно, чтобы голос оригиналда на руссокм модно было обработать и нацчить ему модель.
-- Некоторые модели не влазили в GPU RAM. Были слишьком тыжелые. Сейчас истуация изменилась - установлена новая видео GPU карта 24GB, поэтому мы можем вернуться к тяжелым моделям.
-- Некоторые проекты которые мы пробовали слишьком тяжело настраивались и давали ужасные результаты даже при длительном обучении.
-- Некоторые модели, зхотя и научилиь более или мене говорить, но совершенно не имелт никакого управления темпом или паузами. Так как англйискоий язык гораздо компактнее русского, то новый голос читал текст с огромной скоростью не давая возможности синхронизировать аудиодородку с видео рядом

Пролшло уже очнеь много времени с момнета как мы раюотали наж этими проетками. С того времения вышли новые модели или обновления старых. Я бы хотел вернуться к этому проекту.

Задача взять большой dataset оригинального голоса на русском и нацчить модель разговаривать этим голом на английсокм. У нас много видео лекйия на русском. Их нажо продублировать на английсокм тем же голом. При этом надо добиться более или мнее синхронизации новой аудиодорожки с оригинальным видео. На видео схемы - то есть нету лица человека. Поэтому не нужна синхронизация по кадрам и с гумами. Синхронизация дотстаочна в пределах нескольких секунд опаздывания или ускорения - это на тсращно.

Надо пройти по всем проектам, которые уже на сервер, собрать и прочитать докмунетациб по ним, и сделать текцущий анализ текудщшенор состояния. А потом мы осбудим как уи куда дивгаться дальше. 
ЩЗаймись этим и создай мне подробный анализ - собери в се в один файл. Запиши файл на сервер - скажи где он лежит.

Fast Context
Найти все проекты, связанные с voice cloning / TTS / speaker adaptation / fine-tuning на собственном датасете, а также README, docs, setup и результаты экспериментов
Analyzed
/ai
Analyzed
xtts-finetune-webui
Analyzed
vits
Analyzed
vits (GPT-SoVITS) 1
Analyzed
vits (GPT-SoVITS) 2
Analyzed
tort (Tortoise TTS)
Analyzed
ov/OpenVoice
Analyzed
zonos
Analyzed
whisperdub
Analyzed
xtts
Analyzed
xtts-finetune-webui/finetune_models
Analyzed
vits/alltalk_tts/finetune/tmp-trn/training
Analyzed
vits (GPT-SoVITS) 2/GPT-SoVITS/SoVITS_weights_v3
Analyzed
vits (GPT-SoVITS) 2/GPT-SoVITS/GPT_weights_v3
Analyzed
vits (GPT-SoVITS) 1/GPT-SoVITS/SoVITS_weights_v3
Analyzed
tort (Tortoise TTS)/tune_tortoise_autoregressor/fine_tuning/training
Analyzed
ov/OpenVoice/checkpoints_v2
Analyzed
vits/alltalk_tts/finetune/tmp-trn/training/XTTS_FT-April-05-2025_02+02PM-3d4b94b
Analyzed
vits/alltalk_tts/finetune/tmp-trn/training/XTTS_FT-April-08-2025_10+40PM-958213d
Analyzed
tort (Tortoise TTS)/tune_tortoise_autoregressor/fine_tuning/training/russian_voice
Analyzed
xtts-finetune-webui/finetune_models/run
Analyzed
xtts-finetune-webui/finetune_models/ready
Analyzed
vits (GPT-SoVITS) 2/GPT-SoVITS/SoVITS_weights
Analyzed
vits (GPT-SoVITS) 2/GPT-SoVITS/GPT_weights
Analyzed
vits (GPT-SoVITS) 1/GPT-SoVITS/SoVITS_weights
Analyzed
tort (Tortoise TTS)/tune_tortoise_autoregressor/fine_tuning/training/russian_voice/finetune
Analyzed
vits (GPT-SoVITS) 1/GPT-SoVITS/GPT_SoVITS/GPT_weights
Analyzed
vits (GPT-SoVITS) 1/GPT-SoVITS/GPT_SoVITS/GPT_weights_v2
Analyzed
vits (GPT-SoVITS) 1/GPT-SoVITS/GPT_SoVITS/GPT_weights_v3
Analyzed
vits (GPT-SoVITS) 2/GPT-SoVITS/GPT_weights_v3
Analyzed
vits (GPT-SoVITS) 2/GPT-SoVITS/SoVITS_weights_v2
Analyzed
vits (GPT-SoVITS) 2/GPT-SoVITS/SoVITS_weights
Analyzed
vits (GPT-SoVITS) 1/GPT-SoVITS
Analyzed
vits (GPT-SoVITS) 2/GPT-SoVITS
Analyzed
vits (GPT-SoVITS) 1/GPT-SoVITS/GPT_SoVITS/GPT_weights_v3
Analyzed
vits (GPT-SoVITS) 1/GPT-SoVITS/GPT_SoVITS/SoVITS_weights_v3
Analyzed
vits (GPT-SoVITS) 2/GPT-SoVITS/GPT_weights_v3
Analyzed
vits (GPT-SoVITS) 2/GPT-SoVITS/GPT_SoVITS/SoVITS_weights_v3
Analyzed
vits (GPT-SoVITS) 2/GPT-SoVITS/GPT_SoVITS/GPT_weights_v3
Analyzed
vits (GPT-SoVITS) 1/GPT-SoVITS/GPT_SoVITS/SoVITS_weights
Analyzed
vits (GPT-SoVITS) 2/GPT-SoVITS/GPT_SoVITS/SoVITS_weights
VOICE_CLONING_PROJECTS_AUDIT_2026-02-21.md
new
+271
Готово. Я прошёл по релевантным проектам в ai, собрал текущее состояние и свёл всё в единый подробный отчёт.

Файл отчёта сохранён здесь: VOICE_CLONING_PROJECTS_AUDIT_2026-02-21.md

Ключевые выводы (коротко):

Самый зрелый трек по факту артефактов — XTTS
Есть готовые экспортированные файлы fine-tune в xtts-finetune-webui (@/ai/xtts-finetune-webui/finetune_models/ready/config.json#1-159), плюс исторические тренировочные артефакты в AllTalk с убывающим loss (@/ai/vits/alltalk_tts/finetune/tmp-trn/training/XTTS_FT-April-08-2025_10+40PM-958213d/trainer_0_log.txt#1-105).
GPT-SoVITS
Кодовая база и обновления сильные (@/ai/vits\ (GPT-SoVITS)\ 2/GPT-SoVITS/docs/en/Changelog_EN.md#187-222), но локально многие директории весов пустые; есть следы частичных прошлых экспериментов.
Tortoise
Есть много попыток/архивов, но в активном прогоне не видно финальных .pth в проверенном пути; setup тяжёлый (@/ai/tort\ (Tortoise\ TTS)/tune_tortoise_autoregressor/fine_tuning/training/russian_voice/finetune/train_russian_voice_250322-231616.log#1-150).
Zonos / OpenVoice
Перспективны как современные альтернативы (особенно по controllability темпа/стиля), но в локальном состоянии не выглядят как уже доведённый production-трек (@/ai/zonos/Zonos/README.md#78-86, @/ai/ov/OpenVoice/README.md#25-37).
Для синхронизации с видео
В whisperdub уже есть сильная постановка pipeline и логика тайминга (@/ai/whisperdub/docs/Постановка\ задачи.md#81-99).
Если хочешь, следующим шагом сделаю сравнительную матрицу “XTTS vs GPT-SoVITS v3 vs Zonos” именно под твой кейс (RU voice dataset -> EN dubbing + controllable pace + sync tolerance).

Feedback submitted



Добавь в этот свой файл-отчет полное описание моей зхадачи со всеми нбансами как ты из понимаешь
Задай мне вопосы до начала работы чтобы удебиться что ты правильно понимае задчу

Отлично. Перед тем как править файл, хочу зафиксировать постановку задачи максимально точно.

Подтверди, пожалуйста, ответы на вопросы:

Язык описания в отчёте
Оставляем описание задачи в файле на English (как сейчас), или добавить этот раздел на Russian?
(С учётом твоего правила “all code/docs in English”, по умолчанию сделал бы English.)
Формат блока в отчёте
Добавить как отдельный крупный раздел, например:
## 0) User Task Definition (Detailed)
в начале файла — ок?
Уровень детализации
Нужен максимально полный формат с подпунктами:
Goal / Non-goals
Input assumptions (RU dataset, EN output)
Quality targets (voice similarity, naturalness)
Sync constraints (allowed drift in seconds)
Control requirements (pace, pauses, prosody)
Hardware constraints (24GB VRAM)
Risks / acceptance criteria
Deliverables
Подтверди, что именно такой уровень нужен.
Критерий “похоже на оригинал”
Хочешь, чтобы я зафиксировал в тексте измеримые KPI (например, subjective MOS + speaker similarity score + AB tests), или оставить качественную формулировку без чисел?
Синхронизация с видео
Правильно понимаю целевой допуск:
не нужен lip-sync,
допустим сдвиг в пределах нескольких секунд,
приоритет — управляемая скорость речи и паузы для подгонки тайминга?
Если есть точный порог (например, до 2–3 сек на блок/минуту), укажи.
Технический фокус в формулировке
Включать ли явный приоритет:
сначала оценка уже имеющихся треков (XTTS / GPT-SoVITS / Zonos),
затем выбор 1 primary + 1 backup направления,
затем запуск нового цикла экспериментов?
Ограничения по данным
Нужно ли отдельно прописать требования к датасету (чистка, сегментация, длительности клипов, транскрипты), или это вынести в следующий документ/этап?
Объём текста
Хочешь 1 очень подробный раздел (примерно 1.5–3 страницы в markdown) или компактно (до 1 страницы)?
Как только ответишь — сразу внесу изменения в VOICE_CLONING_PROJECTS_AUDIT_2026-02-21.md.

Feedback submitted



1. все что уже на английском оставь на английском. Но описание задачи напиши на русском.
2. Отдельным блоком в начале файла
3. Сильно детальный. Очень важна Control requirements (pace, pauses, prosody)
Важна Quality targets (voice similarity, naturalness)
Все остальное тоже осатвь.
Риски /acceptance не важны - можно пропустить
4. нет, протсо обшее описание, что похоже на оригинал
5. Да., все верно. Изображения людей на видео вообщзе нет. Это нацчные схемы. Важна синзронизация по блокам, допуск в несколько секунд нормальны. Ожнако, когда очень длинный тест, английский очень ухеодит вперед, потому что сам язык очнеь компактный относитльено русского. Нужно управление темпом и паузами без ухудшения натуральности речи.
6. Да
7. нет пока нет необходиимости
8. компактно (до 1 страницы)?

VOICE_CLONING_PROJECTS_AUDIT_2026-02-21.md
+42
Сделал. Добавил в начало отчёта отдельный детальный блок на русском с твоей постановкой задачи и всеми ключевыми нюансами, включая приоритет на:

Quality targets (voice similarity, naturalness),
Control requirements (pace, pauses, prosody),
синхронизацию по блокам без lip-sync, с допустимым сдвигом в несколько секунд,
проблему “английский уходит вперёд” на длинных фрагментах.
Где именно:
@/ai/VOICE_CLONING_PROJECTS_AUDIT_2026-02-21.md#3-43

Остальной отчёт на английском оставил без изменений.

Feedback submitted



Я обновил файл, VOICE_CLONING_PROJECTS_AUDIT_2026-02-21.md новой информацией. Я туда добавил анализ того, что у меня нету на севере, но есть на локальном компьбтере. Давай перечитай файл и давай снова проанализируем ситуацию

Принял. Перечитал обновлённый файл и даю обновлённый анализ ситуации с учётом нового addendum про локальный компьютер.

Что изменилось по сути
Главное новое — у тебя есть не только серверные эксперименты с моделями, но и локально уже частично рабочий pipeline (audio detach → ASR → reblock → verbalize/translate) @/ai/VOICE_CLONING_PROJECTS_AUDIT_2026-02-21.md#317-356.
Это сильно меняет стратегию: узкое место теперь не “какую модель выбрать”, а “как быстро довести back half до end-to-end”.

Обновлённая картина (кратко)
Front half pipeline уже есть (локально)
Реально присутствуют рабочие скрипты и orchestration @/ai/VOICE_CLONING_PROJECTS_AUDIT_2026-02-21.md#321-355.
Значит, старт не с нуля.
Back half отсутствует как production scripts
Нет реализованных модулей TTS/sync/join/mux в том виде, как нужно для конвейера @/ai/VOICE_CLONING_PROJECTS_AUDIT_2026-02-21.md#376-391.
Это и есть основной blocker для результата.
Модели на сервере — это assets, а не готовый продукт
XTTS даёт лучший continuity baseline (есть артефакты), но без sync-контроля проблема “English drift” останется @/ai/VOICE_CLONING_PROJECTS_AUDIT_2026-02-21.md#266-269.
Твоя формулировка цели стала точнее
Теперь явно зафиксировано, что можно и обновлённые модели смотреть, и совсем новый стек брать — но под строгие требования pace/pauses/prosody + naturalness @/ai/VOICE_CLONING_PROJECTS_AUDIT_2026-02-21.md#31-33, @/ai/VOICE_CLONING_PROJECTS_AUDIT_2026-02-21.md#17-27.
Мой пересмотренный вывод
Оптимальный путь сейчас: pipeline-first, model-second.
То есть:

Дособрать минимально рабочий back half (4 модуля: synth/sync/join/mux).
Подключить XTTS как baseline engine (потому что уже есть рабочие следы).
В тот же интерфейс подключить 1 “control-oriented” альтернативу (Zonos или GPT-SoVITS v3).
Сравнивать модели не “на слух отдельно”, а в едином дубляжном контуре по drift и натуральности @/ai/VOICE_CLONING_PROJECTS_AUDIT_2026-02-21.md#398-423.
Иначе будет повтор старого цикла: “меняем модели, но продукт не сходится по таймингу”.

Что я бы считал текущим статусом проекта
Готовность инфраструктуры: средняя (front half есть, back half нет).
Готовность модельных артефактов: средняя/хорошая для XTTS baseline, фрагментарная для остальных.
Готовность к production dubbing: низкая, пока не закрыт sync+assembly контур.
Следующий практический шаг (самый важный)
Если идём дальше, я предлагаю следующим сообщением сделать очень конкретный execution plan на 2 недели:

какие именно 4 недостающих скрипта сделать сначала,
какие I/O контракты между ними зафиксировать,
как встроить pace/pauses/prosody control без деградации naturalness,
и как измерять drift на длинных лекциях.
Если хочешь — сразу распишу этот план в формате “Task → Output file → Acceptance check”.

Feedback submitted



Нет, я не согласен. Моя глобальная гдавная цель получить искомый результат. Тот готовый pipline который уже есть плохо работал. Иначе я бы не стал заниматься этим всем сначала. Так что я не хочу основываться на готовых решениях которые я уже использовал. Я хотел бы пересмотреть подход, определить, что нового произошло на рынке за последний год, какие новые, совсем другие модели  или opensorce проекты вышли, что обновилсоь в моделях, которые я уже испольовал, какие новые модели вышли и так далее.
Я хочу сделать большой и внимательный Deep Reserch
Всю информацию с сервера и с локального диска я собирал воедино, чтобы отталкиваться от уже проделаной работы, понимать что уже попробовали и не сработало или сработало плохо. Поэтому мы не будет использовать готвоый pipline, но будем искать правильные оптимальные современные решения не забывая об ошибках и проблемах которые уже делали, что бы не делать снова то же самое и чтобы не упереться в те же проблемы, которые уже у нас были ранее.

КРоме того, я хочу разбить общую задачу на две под задачи и с самого начала заняться первой.
Мне надо научиться генерировать голос на, который был бы максимально похожим на оригинал и умел начитывать готовый текст на английском.= К синхронизации это не имеет отношения. Однако нужно учетсь в выборе пути для реализации этой превой под-задачи все нбансы и все критерии, которые мы огоорилил
Вторая под-задача - синхронизация - остается за кадром сейчас. Мы сейчас не будет ей загниматься.

Задай мне ещёъ вопросы, чтобы мы занли что друг дргуа полноьбю бпоняли правильно

Принял фокус:

Сейчас только под-задача №1: получить максимально похожий на оригинал голос, который качественно читает готовый English text.
Под-задачу №2 (sync) пока полностью откладываем.
Готовый старый pipeline не берём как базу, используем его только как источник lessons learned.
Я учёл твои правила из памяти: отвечаю кратко и по делу, без лишней архитектурной “революции”.

Чтобы мы точно синхронизировались перед Deep Research, ответь на вопросы:

A. Target outcome (что считаем успехом)
Что для тебя важнее в под-задаче №1:
voice similarity (макс. похожесть),
natural English pronunciation,
баланс 50/50?
Нужен один фиксированный голос (один спикер) или сразу поддержка нескольких голосов?
Какой формат результата нужен на этом этапе:
CLI inference,
Python API,
WebUI,
или без разницы, главное качество?
B. Данные и обучение
Сколько примерно часов русского аудио у тебя реально доступно для этого спикера (порядок: 1–5 / 5–20 / 20+ / 100+)?
Есть ли у тебя чистые транскрипты для этого русского датасета, или часть данных только аудио без текста?
Ты хочешь в под-задаче №1:
только zero/few-shot cloning без обучения,
или обязательно fine-tuning / speaker adaptation?
C. Compute / practical constraints
На каком железе планируем основной запуск экспериментов:
только твоя локальная 24GB GPU,
сервер(а),
гибрид?
Есть ограничение по времени на один эксперимент (например, “не больше N часов/суток”)?
Допускаешь коммерчески-ограниченные лицензии моделей, или только permissive open-source (MIT/Apache/BSD)?
D. Scope of Deep Research
Под “за последний год” берём период примерно 2025-01 → 2026-02 — ок?
В Deep Research включать только open-source self-hosted проекты, или также закрытые API/hosted решения для benchmarking?
Какой формат финального ресёрча хочешь:
короткий shortlist (5–8 кандидатов),
или большой longlist (15+ кандидатов) с детальной сравнительной таблицей?
E. Decision framework
После Deep Research ты хочешь получить:
1 основной кандидат + 1 backup,
или 2–3 кандидата для практического bake-off?
Нужен ли сразу план PoC для под-задачи №1 (datasets, eval, first runs), или пока только аналитический отчёт по рынку/моделям?
Когда ответишь, я начну именно Deep Research по modern voice cloning/TTS landscape под твой фокус (без sync), с учётом того, что уже пробовали и что не сработало.

Feedback submitted



А.
1. важнее - voice similarity ( (макс. похожесть), natural English pronunciation меньше принципиальна. Я бы сказал 60 к 40, примерно.
2. А при чем тут несколько головов если мы клонируем конретный голос? Мы клонируем голос и модель должна владеть именно этим голосом. Если мы склонируем второй голос, то она будет владеть двумя. В этом контексте я не совсем уверен, что понял твой вопрос про "один спикер) или сразу поддержка нескольких голосов"
3. Не понимаю вопроса. При чем туту формат результата? Голос на выходе - это аудиофайл. При чем тут то , что ты спросил, поясни твой контекст вопроса. 

B.
4. Столько, сколько надо. Могу сделать 20 минут, могу час, могу 10 часов. Желательно иметь гибкость, то есть дать 5 минут - посмотреть рещультат. если илет нормально но надо больше - дать 30 минут. Если заранее известно, что нужно несколько часов можно подготовить заранее. Одннако, не хотелось бы их готовить харанее, если они не нужны или чтобы потестировать и понять6 что это не работает. Хочется не терять время6 но если есть увереность, что что-то нужно, например много часов данных, то я изх предоставлю.
5. есть и так и так. Если можно без транскрипта - это лучше. Но если нужно подготовить с транскриптом 0 я подготовлю. Это не должно быть причиной выбора pipline. 
6. zero/few-shot cloning без обучения по моему опыту не работают. Я пробовал много раз. Я слабо верб, что даже если прошло много времени в этом плане многое изменилось. Скорее всего нет. Я конечно готов опять попробовать если действительно появилось что-то координально новое за послдежнее время, я вно отличающееся по качеству от того, что я уже пробовал ( у тебя есть вся информауибю о том, что я пробовал ранее). 
Именно поэтому я бы больше склонялся к fine-tuning

Ожилай следующих ответов в следующем сообщении; Я не закончил отвечать

Принял, жду твою вторую часть ответов.

Коротко поясню контекст двух вопросов, которые были неочевидны:

Про “один/несколько спикеров”
Ты прав: для текущей цели — один конкретный голос.
Я спрашивал это только чтобы понять, нужен ли сразу multi-speaker сценарий в архитектуре экспериментов.
Фиксируем: single-speaker clone.
Про “формат результата (CLI/API/WebUI)”
Это не про итоговый audio (он в любом случае WAV/MP3), а про способ запуска экспериментов:
CLI обычно быстрее для batch-оценки,
WebUI удобнее для ручного прослушивания,
API удобно для автоматизации тестов.
Но если тебе это сейчас неважно — ок, не будем этим ограничивать выбор.
Также зафиксировал уже полученное от тебя:

приоритет: voice similarity ~60%, natural English pronunciation ~40%,
data strategy: нужна гибкость по объёму (быстрые пробы на малом, масштабирование при успехе),
transcripts: желательно без них, но при необходимости подготовишь,
основной вектор: fine-tuning, zero/few-shot только если реально появился сильный прорыв.
Жду продолжение ответов (блоки C/D/E).

Feedback submitted



2. формат результата - не важно на данном этапе. не будем этим ограничивать выбор.

C.
только моя локальная 24GB GPU,

Ограничения по времени на один эксперимент нету

Допускаю коммерчески-ограниченные лицензии модели. Но для меня должно быть бесплатно. Платные варинаты не рассматриваются.

D. Scope of Deep Research
берём период примерно с сентября 2025 года

Включать только open-source self-hosted проекты или open-source модели, которые можно испольщовать у себя. Не важно что, но бесплатно. если морджно бесплатно у чсебя что-0то что коммерческое но они дают установить и испольщовать для не коммерческого испольщования –  тоже подойдет.

результат - короткий shortlist (5–8 кандидатов),

E. Decision framework
После Deep Research я хочешь получить:
или 2–3 кандидата для практического bake-off но с рекоммендацией с чего начать и почему. Сранить все варинаты тчточьы я мог выбрать.

пока только аналитический отчёт по рынку/моделям

1
Собрать market scan (Sep 2025–Feb 2026): новые open-source/self-hosted TTS/voice-cloning модели, их лицензии, поддержка fine-tuning/speaker-adaptation, требования к данным и GPU.

Сопоставить кандидатов с твоими критериями (voice similarity 60/40, RU voice -> EN text, fine-tuning предпочтителен, бесплатно, 24GB GPU) и исключить заведомо неподходящие.

Сформировать shortlist 5–8 кандидатов и выбрать 2–3 для практического bake-off (с рекомендацией порядка запуска).

Собрать аналитический отчёт: таблица сравнения + заметки 'что нового' и 'почему может/не может решить твою задачу'.

Понял. Тогда я начинаю именно с Deep Research (Sep 2025 → сейчас) по бесплатным self-hosted/open-source решениям для voice cloning via fine-tuning / speaker adaptation под твой кейс (RU voice → EN text, similarity важнее pronunciation, 24GB GPU). Дальше: соберу кандидатов, проверю лицензии/реальную пригодность, и выдам shortlist 5–8 + рекомендации 2–3 для bake-off. Сейчас запущу web search по новым моделям и обновлениям старых.

Начинаю Deep Research по новым/обновившимся open/free решениям с сентября 2025: прочитаю ключевые GitHub README/лицензии и наличие fine-tuning/LoRA/voice cloning, затем соберу shortlist 5–8 и рекомендую 2–3 для bake-off под твой критерий voice similarity (60/40) на одной 24GB GPU. Сейчас запрошу содержимое основных репозиториев.

Created outline

github.com
Created outline

github.com
Created outline

github.com
Created outline

github.com
Created outline

github.com
Created outline

github.com
Created outline

github.com
Analyzed content
7 chunks
Analyzed content
3 chunks
Analyzed content
4 chunks
Analyzed content
2 chunks
Analyzed content
3 chunks
Analyzed content
2 chunks
Analyzed content
3 chunks
Analyzed content
6 chunks
Analyzed content
4 chunks
Analyzed content
Key Features
Analyzed content
2 chunks
Analyzed content
2 chunks
Продолжаю Deep Research: сейчас доберу по каждому кандидату самое важное — license, наличие fine-tuning/LoRA, поддерживаемые языки, и что именно даёт максимальную voice similarity в твоём кейсе (RU voice → EN text). Затем соберу shortlist 5–8 и рекомендую 2–3 для bake-off. Сейчас дочитаю ключевые разделы README (license + finetune).

Analyzed content
7 chunks
Analyzed content
Clone and install
Analyzed content
Model download
Analyzed content
5 chunks
Analyzed content
6 chunks
Analyzed content
6 chunks
Analyzed content
6 chunks
Analyzed content
6 chunks
Analyzed content
License
Analyzed content
5 chunks
Ок, по моделям, которые “вышли/сильно обновились” с сентября 2025, уже видно несколько реально новых сильных направлений (Apache-2.0, LoRA fine-tuning, voice cloning). Сейчас дочитаю ещё 4–5 ключевых репозиториев (IndexTTS, Chatterbox, Higgs Audio, VibeVoice, OuteTTS), чтобы точно зафиксировать license + наличие fine-tuning — и после этого соберу твой shortlist 5–8 и рекомендацию 2–3 для bake-off.

Created outline

github.com
Created outline

github.com
Created outline

github.com
Created outline

github.com
Created outline

github.com
Analyzed content
3 chunks
Analyzed content
🔥 IndexTTS2 Quickstart
Analyzed content
7 chunks
Analyzed content
3 chunks
Analyzed content
6 chunks
Analyzed content
5 chunks
Analyzed content
6 chunks
Analyzed content
📰 News
Analyzed content
9 chunks
Analyzed content
Basic Usage
Analyzed content
7 chunks
Created outline

raw.githubusercontent.com
Failed to fetch document content atraw.githubusercontent.com
Created outline

raw.githubusercontent.com
Failed to fetch document content atraw.githubusercontent.com
Created outline

raw.githubusercontent.com
Analyzed content
Chunk 0
Analyzed content
Chunk 0
Analyzed content
Chunk 0
Analyzed content
9 chunks
Created outline

github.com
Created outline

github.com
Analyzed content
2 chunks
Analyzed content
License
Analyzed content
2 chunks
Analyzed content
2 chunks
Analyzed content
3 chunks
Analyzed content
⚡ Model Zoo
Analyzed content
License
Created outline

speech.fish.audio
Created outline

speech.fish.audio
Created outline

huggingface.co
Analyzed content
4. Finally, fine-tuning with LoRA
Analyzed content
3 chunks
Created outline

raw.githubusercontent.com
Created outline

github.com
Read page

raw.githubusercontent.com
Analyzed content
Technical Details
Analyzed content
3 chunks
Analyzed content
6 chunks
Read page

raw.githubusercontent.com
Created outline

raw.githubusercontent.com
Read page

raw.githubusercontent.com
Failed to fetch document content atraw.githubusercontent.com
Собрать market scan (Sep 2025–Feb 2026): новые open-source/self-hosted TTS/voice-cloning модели, их лицензии, поддержка fine-tuning/speaker-adaptation, требования к данным и GPU.

2
Сопоставить кандидатов с твоими критериями (voice similarity 60/40, RU voice -> EN text, fine-tuning предпочтителен, бесплатно, 24GB GPU) и исключить заведомо неподходящие.

2 more
VOICE_CLONING_DEEP_RESEARCH_SINCE_2025-09.md
new
+173
2 more
Сформировать shortlist 5–8 кандидатов и выбрать 2–3 для практического bake-off (с рекомендацией порядка запуска).

4
Собрать аналитический отчёт: таблица сравнения + заметки 'что нового' и 'почему может/не может решить твою задачу'.

Read page

raw.githubusercontent.com
Failed to fetch document content atraw.githubusercontent.com
Failed to fetch document content atraw.githubusercontent.com
Failed to fetch document content atraw.githubusercontent.com
Failed to fetch document content atraw.githubusercontent.com
Created outline

raw.githubusercontent.com
Я учёл все новые данные и ошибки Not Found: это просто значит, что в некоторых репозиториях нет файла LICENSE по ожидаемому пути (например, у chatterbox license лежит в ветке master, а у kani-tts-2 лицензия оказалась в pyproject.toml, а не отдельным файлом). Сейчас я:\n\n- обновлю VOICE_CLONING_DEEP_RESEARCH_SINCE_2025-09.md:\n - добавлю KaniTTS-2 (лицензия/роль/почему это скорее comparator)\n - добавлю Step-Audio2 и VibeVoice (почему они слабее релевантны для Sub-task #1)\n - уточню IndexTTS2 license (он не Apache/MIT)\n- затем дам тебе итоговый shortlist 5–8 + рекомендованные 2–3 для bake-off (с чего начинать и почему).\n\nДелаю правку файла сейчас.

VOICE_CLONING_DEEP_RESEARCH_SINCE_2025-09.md
+39
-7
Что я сделал и где результат
Я завершил Deep Research (Sep 2025 → Feb 2026) под твою Sub-task #1 (voice similarity приоритет, RU voice → EN text, fine-tuning предпочтителен, бесплатно, 24GB GPU).
Итоговый аналитический отчёт лежит здесь:
/ai/VOICE_CLONING_DEEP_RESEARCH_SINCE_2025-09.md
В нём:

shortlist 5–8 кандидатов,
рекомендация 2–3 для bake-off (с чего начать и почему),
пояснения по license, fine-tuning/LoRA, RU/EN пригодности,
и что я считаю “риском повторить старые проблемы”.
Ключевая выжимка (shortlist + 2–3 для bake-off)
Shortlist (5–8) под твою цель
Tier-1 (наиболее “в цель” под fine-tuning single-speaker RU→EN):

Qwen3-TTS (CustomVoice fine-tuning) — Apache-2.0, есть явный single-speaker fine-tune pipeline.
CosyVoice 3.0 / 2.0 — Apache-2.0, заявляет сильную speaker similarity + prosody + instruct control.
FishAudio-S1 (Fish Speech) — Apache-2.0, есть LoRA fine-tune, но важно: по их же докам, timbre может не “зафиксироваться” без правильного режима.
Tier-2 (супер-важные современные baseline/comparator): 4. Chatterbox-Multilingual — MIT, сильный zero-shot comparator (быстро понять, насколько “рынок ушёл вперёд”). 5. Higgs Audio v2.5 — Apache-2.0, очень сильный foundation-model benchmark, но fine-tune story не очевиден.

Дополнительно (как “новая волна”, но не явный fine-tune путь): 6. KaniTTS-2 — repo декларирует Apache-2.0 в pyproject.toml, но есть противоречивые classifiers; как comparator ок, как main path пока неочевидно.

Ситуативные/осторожно: 7. IndexTTS2 — важное: не Apache/MIT, у него Bilibili Model Use License Agreement (кастомная лицензия). Плюс duration control заявлен, но “не включён в релизе”. 8. VoxCPM 1.5 — Apache-2.0 и очень удобный LoRA/SFT, но он ZH/EN-first, и для твоего RU training это риск.

Рекомендованные 2–3 кандидата для первого bake-off
Qwen3-TTS fine-tune
Потому что это самый “прямой” современный путь именно к твоему формату: single-speaker SFT, RU поддерживается, лицензия чистая.
CosyVoice 3.0/2.0
Потому что это сильный конкурент по speaker similarity/prosody, и тоже RU/EN в зоне покрытия.
Chatterbox-Multilingual (или вместо него “новая волна”: Higgs v2.5)
Не потому что ты веришь в zero-shot, а чтобы быстро ответить на вопрос: действительно ли за год zero-shot стал настолько лучше, что fine-tuning может оказаться не нужен (или нужен существенно меньше).
Важные уточнения (чтобы не повторить старые тупики)
Требование “без транскриптов”: почти все реальные fine-tuning пайплайны в 2025–2026 всё ещё завязаны на transcripts.
Даже Qwen3-TTS fine-tuning JSONL требует text и ref_audio. Это не значит “нельзя”, но значит что pipeline выбора модели не должен основываться на надежде “вообще без текстов”.
Главный practical фильтр для твоей задачи:
не “умеет voice cloning”, а умеет стабильно удерживать одну личность голоса при:
длинном тексте,
разных темах,
и при cross-lingual (RU speaker identity → EN content).
Следующий шаг (вопрос к тебе)
Ты хочешь, чтобы я:

добавил этот Deep Research как раздел в существующий VOICE_CLONING_PROJECTS_AUDIT_2026-02-21.md (кратко + ссылка на отдельный файл),
или
оставить как отдельный документ и дальше обсуждать план bake-off (какие 3 теста, какой минимум данных, какие критерии “похож/не похож” без метрик)?
Статус: Deep Research завершён, shortlist и bake-off рекомендации готовы.

Feedback submitted



сделай отдельный документ

Отдельный документ уже сделан:
VOICE_CLONING_DEEP_RESEARCH_SINCE_2025-09.md

Хочешь, чтобы я дополнительно:

сделал отдельный 1-page summary (shortlist + 2–3 для bake-off) в новом файле, или
просто добавил ссылку на этот документ в твоём основном VOICE_CLONING_PROJECTS_AUDIT_2026-02-21.md (без копипасты текста)?
Статус: отдельный документ создан и готов.

Feedback submitted



Давай тогда приступим к одном уиз варинатов. Попробуем Qwen3-TTS ?

Да, давай. Я предлагаю начать с Qwen3-TTS-12Hz-0.6B-Base (на 24GB обычно проще и быстрее для первого цикла), а уже после первого успешного bake-off при необходимости перейти на 1.7B. Сейчас:\n\n1) Проверю, что у тебя уже есть в workspace (папки/датасет/скрипты).\n2) Составлю пошаговый план: env → подготовка train_raw.jsonl → извлечение audio_codes → SFT → быстрый inference-чек.\n3) Дальше дам команды, которые можно выполнить (ничего не запускаю без подтверждения).\n\nСначала посмотрю структуру ai.

Analyzed
/ai
Ок, идём с Qwen3-TTS. Дальше нужно два куска информации:

Данные: где лежит твой датасет (папка с *.wav) и есть ли уже транскрипты (текст для каждого аудио)?
Окружение: я проверю GPU/conda/python, затем предложу команды для установки qwen-tts, подготовки train_raw.jsonl, извлечения audio_codes, SFT и короткого inference-теста.
Сейчас обновлю план и параллельно подтяну официальный README Qwen3-TTS (install/requirements).

1
Подтвердить входные данные для fine-tuning: путь к WAV датасету, наличие transcript для каждого клипа, один reference audio для speaker identity, целевой размер/длительность клипов.

Проверить окружение (CUDA/GPU, python/conda) и поднять env под Qwen3-TTS + установить зависимости (`qwen-tts`).

Подготовить `train_raw.jsonl` и прогнать `prepare_data.py` для извлечения `audio_codes`.

Запустить SFT (`sft_12hz.py`) на 0.6B и сделать быстрый inference-чек (генерация EN текста голосом target speaker).

Feedback submitted



Так а в какой папке ты собираешщься все это делать? Не спеши, давай осудим сначала

1
Согласовать рабочую папку/структуру проекта для эксперимента Qwen3-TTS (код, данные, чекпоинты, выходные wav, кэши).

Подтвердить входные данные для fine-tuning: путь к WAV датасету, наличие transcript для каждого клипа, один reference audio для speaker identity, целевой размер/длительность клипов.

Проверить окружение (CUDA/GPU, python/conda) и поднять env под Qwen3-TTS + установить зависимости (`qwen-tts`).

Подготовить `train_raw.jsonl` и прогнать `prepare_data.py` для извлечения `audio_codes`.

Запустить SFT (`sft_12hz.py`) на 0.6B и сделать быстрый inference-чек (генерация EN текста голосом target speaker).

Где делать эксперимент (предложение структуры)
Я бы делал всё в отдельной “песочнице”, чтобы:

не смешивать с твоими существующими xtts/, vits/, tort/ и т.п.
можно было просто удалить папку и “откатиться”
пути в командах были короткими и стабильными
Вариант A (рекомендую): отдельная папка под эксперимент
Например:

/ai/experiments/qwen3_tts_ru_speaker_en/
repo/ — клон QwenLM/Qwen3-TTS (только код)
data/ — твой датасет (лучше symlink внутрь, чтобы не копировать гигабайты)
manifests/ — train_raw.jsonl, train_with_codes.jsonl, возможно val.jsonl
runs/ — результаты обучения
runs/output/checkpoint-epoch-*
samples/ — сгенерированные *.wav для быстрых сравнений
notes/ — короткие заметки “что запускали, какими параметрами”
Почему так удобно для Qwen3-TTS:

output_model_path (из sft_12hz.py) указывает прямо в runs/output
манифесты живут отдельно и их легко версионировать/сравнивать
Вариант B: внутри models/ (не рекомендую)
Можно под /ai/models/..., но у тебя models/ уже выглядит как общий склад, и туда легко “навалить” артефактов от экспериментов.

Что я НЕ предлагаю делать
Не складывать веса/кэши внутрь repo/ (будет грязно и тяжело).
Не копировать датасет без необходимости (лучше symlink/указать абсолютный путь в JSONL).
2 важных решения перед стартом (нужно твое ОК)
Где держать HuggingFace cache с моделями/токенайзером?
~/.cache/huggingface (дефолт, просто)
или /ai/models/hf_cache (удобно, если домашняя директория маленькая/хочешь всё в одном месте)
Как подключаем датасет в эксперимент?
symlink в .../data/ (предпочтительно)
или оставляем на месте и в JSONL пишем абсолютные пути
Вопросы, чтобы зафиксировать папку и двигаться дальше
[dataset_path] Где сейчас лежит твой RU-датасет (.wav + тексты)?
[size] Примерно сколько аудио и сколько часов?
[ref_audio] Есть ли один “идеальный” ref.wav (10–30 секунд) для speaker identity, который будем ставить как ref_audio для всех строк?
Если скажешь “давай Вариант A” и ответишь на 3 вопроса выше — я зафиксирую точные пути и дальше уже составлю команды под твою структуру (без запуска, пока не подтвердите).

Feedback submitted



Тогда так:
Я создал на github repository https://github.com/Mushkrot/Qwen3TTS


Соаздай новую паку /ai/Qwen3TTS скачав репозиторий
Создай в ней папку docs и перенеси туда наши два файла, которые мы сгенерировали VOICE_CLONING_PROJECTS_AUDIT_2026-02-21 и VOICE_CLONING_DEEP_RESEARCH_SINCE_2025-09
Создай виртуальное окружение для питона в этой папке.

Сделай первый commit и push


Ок, сделаю это в несколько безопасных шагов: проверю, что /ai/Qwen3TTS ещё не существует, затем клонирую твой GitHub repo, создам docs/, перенесу туда два markdown-файла, создам Python venv (в .venv/), добавлю .gitignore чтобы venv не попал в git, после чего сделаю первый commit и push. Сейчас начну с проверки папки.

1
Проверить, что /ai/Qwen3TTS не существует/пустая и можно клонировать репозиторий.

Склонировать https://github.com/Mushkrot/Qwen3TTS в /ai/Qwen3TTS.

Создать /ai/Qwen3TTS/docs и перенести туда два markdown файла аудита и deep research.

Создать Python virtual environment в /ai/Qwen3TTS/.venv и добавить .gitignore для исключения .venv.

Сделать первый git commit и push в origin.

Command git

git clone https://github.com/Mushkrot/Qwen3TTS Qwen3TTS
Cloning into 'Qwen3TTS'...
remote: Enumerating objects: 4, done.
remote: Counting objects: 100% (4/4), done.
remote: Compressing objects: 100% (3/3), done.
remote: Total 4 (delta 0), reused 0 (delta 0), pack-reused 0 (from 0)
Receiving objects: 100% (4/4), done.


Using legacy terminal
Configure
1 more
Склонировать https://github.com/Mushkrot/Qwen3TTS в /ai/Qwen3TTS.

3
Создать /ai/Qwen3TTS/docs и перенести туда два markdown файла аудита и deep research.

2 more
Analyzed
Qwen3TTS
Command mkdir, mv in Qwen3TTS

mkdir -p docs && mv ../VOICE_CLONING_PROJECTS_AUDIT_2026-02-21.md docs/ && mv ../VOICE_CLONING_DEEP_RESEARCH_SINCE_2025-09.md docs/

Using legacy terminal
Configure
Command python3 in Qwen3TTS

python3 -m venv .venv

Using legacy terminal
Configure
3 more
Создать Python virtual environment в /ai/Qwen3TTS/.venv и добавить .gitignore для исключения .venv.

5
Сделать первый git commit и push в origin.

Command git in Qwen3TTS

git status -sb
## main...origin/main
?? docs/


Using legacy terminal
Configure
Analyzed
Qwen3TTS/docs
Command git in Qwen3TTS

git add -A && git commit -m "Add voice cloning research docs" -m "Add generated audit and deep research markdown files under docs/."
[main ce49941] Add voice cloning research docs
 2 files changed, 626 insertions(+)
 create mode 100644 docs/VOICE_CLONING_DEEP_RESEARCH_SINCE_2025-09.md
 create mode 100644 docs/VOICE_CLONING_PROJECTS_AUDIT_2026-02-21.md


Using legacy terminal
Configure
Остался последний шаг: push в origin/main. Перед этим быстро проверю git status, чтобы убедиться, что в коммит попали только docs/* (а .venv не трекается), и затем выполню git push.

Command git in Qwen3TTS

git status -sb
## main...origin/main [ahead 1]


Using legacy terminal
Configure
Command git in Qwen3TTS

git push
Enumerating objects: 6, done.
Counting objects: 100% (6/6), done.
Delta compression using up to 12 threads
Compressing objects: 100% (5/5), done.
Writing objects: 100% (5/5), 13.51 KiB | 13.51 MiB/s, done.
Total 5 (delta 0), reused 0 (delta 0), pack-reused 0
To https://github.com/Mushkrot/Qwen3TTS
   c169bd4..ce49941  main -> main


Using legacy terminal
Configure
Готово
Репозиторий https://github.com/Mushkrot/Qwen3TTS настроен и изменения закоммичены + запушены в main.

Создана папка: Qwen3TTS (клон твоего repo)
Создана папка: docs
Перенесены файлы:
VOICE_CLONING_PROJECTS_AUDIT_2026-02-21.md
VOICE_CLONING_DEEP_RESEARCH_SINCE_2025-09.md
Создано venv: .venv (и он игнорируется .gitignore)
Первый commit: ce49941 (“Add voice cloning research docs”)
Push: выполнен в origin/main
Что дальше (следующий шаг к Qwen3-TTS fine-tune)
Скажи:

где лежит твой датасет (путь),
есть ли транскрипты,
и есть ли один хороший ref_audio (10–30 сек), который будем использовать для всех строк.
Статус: задача по repo/папкам/venv/commit+push завершена.

Feedback submitted



Я теб все положу куда надо. ДЖавай сначало все установим созладим посатвим. а потом я полдуд dataset в том виде, в котором ты скажешь и куда ты скажешь. Не забекгай впередж.
Что наужно дальше чтобы устнаовить все что нам нуно для реализации задачи? Не забегай вперед. Давай обсудим.

Created memory "Qwen3TTS repo bootstrap completed"
Analyzed
Qwen3TTS
Created memory "User prefers install-first then dataset"
Analyzed
Qwen3TTS
Deleted memory "Qwen3TTS repo bootstrap completed"
Updated memory from "User prefers install-first then dataset" to "User prefers install-first then dataset"
Deleted memory "User prefers install-first then dataset"
Created memory "User requested install-first Qwen3-TTS workflow"
Deleted memory "User requested install-first Qwen3-TTS workflow"
Analyzed
Qwen3TTS
Analyzed
Qwen3TTS
Created memory "Qwen3TTS install-first workflow preference"
Analy

git status -sb
Canceled terminal command