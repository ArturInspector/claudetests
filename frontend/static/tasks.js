// Логика для работы с задачами

let currentTask = null;
let codeEditor = null;
let improvedCodeEditor = null;

// Инициализация
document.addEventListener('DOMContentLoaded', async () => {
    await loadTasks();
    
    // Фильтры
    document.getElementById('applyFiltersBtn').addEventListener('click', loadTasks);
    
    // Кнопки
    document.getElementById('backToTasksBtn').addEventListener('click', () => {
        document.getElementById('taskSelection').classList.remove('hidden');
        document.getElementById('taskArea').classList.add('hidden');
    });
    
    document.getElementById('submitCodeBtn')?.addEventListener('click', submitWriteTask);
    document.getElementById('submitReviewBtn')?.addEventListener('click', submitReviewTask);
    document.getElementById('showHintsBtn')?.addEventListener('click', showHints);
});

// Загрузка списка задач
async function loadTasks() {
    const block = document.getElementById('blockFilter').value;
    const language = document.getElementById('languageFilter').value;
    const difficulty = document.getElementById('difficultyFilter').value;
    
    const params = new URLSearchParams();
    if (block) params.append('block', block);
    if (language) params.append('language', language);
    if (difficulty) params.append('difficulty', difficulty);
    
    try {
        const response = await fetch(`/api/tasks?${params.toString()}`);
        const tasks = await response.json();
        
        displayTasks(tasks);
    } catch (error) {
        showNotification('Ошибка загрузки задач', 'error');
    }
}

// Отображение списка задач
function displayTasks(tasks) {
    const container = document.getElementById('tasksList');
    
    if (tasks.length === 0) {
        container.innerHTML = '<div class="card text-center"><p class="text-secondary">Задачи не найдены</p></div>';
        return;
    }
    
    container.innerHTML = tasks.map(task => `
        <div class="card" style="cursor: pointer;" onclick="loadTask(${task.id})">
            <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 1rem;">
                <h3 class="card-title" style="margin: 0;">${task.title}</h3>
                <span class="badge ${task.task_type === 'write' ? 'badge-level' : 'badge-resource'}">
                    ${task.task_type === 'write' ? '✍️ Write' : '🔍 Review'}
                </span>
            </div>
            <p class="text-secondary" style="margin-bottom: 1rem; font-size: 0.875rem;">
                ${task.description.substring(0, 150)}${task.description.length > 150 ? '...' : ''}
            </p>
            <div style="display: flex; gap: 0.5rem; flex-wrap: wrap; margin-bottom: 1rem;">
                <span class="difficulty-badge ${Utils.getDifficultyClass(task.difficulty)}">
                    ${task.difficulty}
                </span>
                <span class="badge badge-tag">${task.language}</span>
                ${task.estimated_time ? `<span class="badge badge-tag">⏱️ ${task.estimated_time} мин</span>` : ''}
            </div>
            <button class="btn btn-primary" style="width: 100%;">Начать</button>
        </div>
    `).join('');
}

// Загрузка задачи
async function loadTask(taskId) {
    try {
        showLoading(true);
        
        const response = await fetch(`/api/tasks/${taskId}`);
        const task = await response.json();
        
        currentTask = task;
        
        // Заполняем заголовок
        document.getElementById('taskTitle').textContent = task.title;
        document.getElementById('taskTypeBadge').textContent = task.task_type === 'write' ? '✍️ Write' : '🔍 Review';
        document.getElementById('taskTypeBadge').className = `badge ${task.task_type === 'write' ? 'badge-level' : 'badge-resource'}`;
        document.getElementById('taskBlockBadge').textContent = task.block === 'write' ? '📝 Написать код' : '🔍 Code Review';
        document.getElementById('taskDifficultyBadge').textContent = task.difficulty;
        document.getElementById('taskDifficultyBadge').className = `difficulty-badge ${Utils.getDifficultyClass(task.difficulty)}`;
        document.getElementById('taskLanguageBadge').textContent = task.language;
        
        // Описание
        document.getElementById('taskDescription').innerHTML = parseMarkdownToHtml(task.description);
        
        // Требования
        if (task.requirements && task.requirements.length > 0) {
            document.getElementById('taskRequirements').innerHTML = `
                <h4 style="margin-bottom: 0.5rem;">Требования:</h4>
                <ul style="margin-left: 1.5rem;">
                    ${task.requirements.map(r => `<li>${r}</li>`).join('')}
                </ul>
            `;
        }
        
        // Показываем нужную секцию
        if (task.task_type === 'write') {
            document.getElementById('writeTaskSection').classList.remove('hidden');
            document.getElementById('reviewTaskSection').classList.add('hidden');
            
            // Инициализируем редактор кода (простой textarea если Monaco недоступен)
            const editorEl = document.getElementById('codeEditor');
            if (!codeEditor) {
                // Простой textarea редактор
                editorEl.innerHTML = '';
                const textarea = document.createElement('textarea');
                textarea.id = 'codeTextarea';
                textarea.style.cssText = 'width: 100%; height: 100%; padding: 1rem; font-family: monospace; font-size: 14px; border: none; resize: none;';
                textarea.value = task.starter_code || '';
                editorEl.appendChild(textarea);
                codeEditor = { getValue: () => textarea.value, setValue: (val) => textarea.value = val };
            } else {
                if (codeEditor.setValue) {
                    codeEditor.setValue(task.starter_code || '');
                } else {
                    const textarea = document.getElementById('codeTextarea');
                    if (textarea) textarea.value = task.starter_code || '';
                }
            }
            
            // Тесты
            if (task.test_code) {
                document.getElementById('testsSection').classList.remove('hidden');
                const codeEl = document.querySelector('#testsCode code');
                codeEl.textContent = task.test_code;
                codeEl.className = `language-${task.language}`;
                hljs.highlightElement(codeEl);
            } else {
                document.getElementById('testsSection').classList.add('hidden');
            }
            
        } else {
            document.getElementById('writeTaskSection').classList.add('hidden');
            document.getElementById('reviewTaskSection').classList.remove('hidden');
            
            // Код от ИИ
            const aiCodeEl = document.querySelector('#aiCode code');
            aiCodeEl.textContent = task.ai_code;
            aiCodeEl.className = `language-${task.language}`;
            hljs.highlightElement(aiCodeEl);
            
            // Вопросы для ревью
            if (task.review_questions && task.review_questions.length > 0) {
                document.getElementById('reviewQuestions').innerHTML = task.review_questions.map((q, idx) => `
                    <div style="margin-bottom: 1rem; padding: 1rem; background: var(--bg-secondary); border-radius: 0.5rem;">
                        <div style="font-weight: 600; margin-bottom: 0.5rem;">${idx + 1}. ${q}</div>
                        <textarea 
                            id="reviewAnswer_${idx}" 
                            placeholder="Твой ответ..."
                            style="width: 100%; min-height: 60px; padding: 0.5rem; border: 1px solid var(--border-color); border-radius: 0.375rem; font-family: inherit;"
                        ></textarea>
                    </div>
                `).join('');
            }
            
            // Редактор для улучшенного кода
            const improvedEditorEl = document.getElementById('improvedCodeEditor');
            if (!improvedCodeEditor) {
                improvedEditorEl.innerHTML = '';
                const textarea = document.createElement('textarea');
                textarea.id = 'improvedCodeTextarea';
                textarea.style.cssText = 'width: 100%; height: 100%; padding: 1rem; font-family: monospace; font-size: 14px; border: none; resize: none;';
                improvedEditorEl.appendChild(textarea);
                improvedCodeEditor = { getValue: () => textarea.value, setValue: (val) => textarea.value = val };
            } else {
                if (improvedCodeEditor.setValue) {
                    improvedCodeEditor.setValue('');
                } else {
                    const textarea = document.getElementById('improvedCodeTextarea');
                    if (textarea) textarea.value = '';
                }
            }
        }
        
        // Скрываем результаты предыдущей попытки
        document.getElementById('compilationResult').classList.add('hidden');
        document.getElementById('reviewResult').classList.add('hidden');
        
        // Показываем область задачи
        document.getElementById('taskSelection').classList.add('hidden');
        document.getElementById('taskArea').classList.remove('hidden');
        
        showLoading(false);
        
    } catch (error) {
        showLoading(false);
        showNotification('Ошибка загрузки задачи', 'error');
    }
}

// Отправка Write задачи
async function submitWriteTask() {
    let userCode;
    if (codeEditor && codeEditor.getValue) {
        userCode = codeEditor.getValue();
    } else {
        const textarea = document.getElementById('codeTextarea');
        if (!textarea) {
            showNotification('Редактор кода не готов', 'error');
            return;
        }
        userCode = textarea.value;
    }
    if (!userCode.trim()) {
        showNotification('Напиши код перед отправкой', 'error');
        return;
    }
    
    try {
        showLoading(true);
        
        const response = await fetch(`/api/tasks/${currentTask.id}/submit`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                user_code: userCode,
                time_spent: 0
            })
        });
        
        const result = await response.json();
        
        // Показываем результат
        const resultDiv = document.getElementById('compilationResult');
        resultDiv.classList.remove('hidden');
        
        if (result.success) {
            resultDiv.className = 'card mb-4';
            resultDiv.style.borderLeft = '4px solid #10b981';
            resultDiv.innerHTML = `
                <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 1rem;">
                    <span style="font-size: 1.5rem;">✅</span>
                    <h3 style="margin: 0; color: #10b981;">Решение принято!</h3>
                </div>
                <p>Все тесты прошли успешно. Отличная работа!</p>
                <p class="text-secondary" style="font-size: 0.875rem; margin-top: 0.5rem;">
                    Попыток: ${result.attempts}
                </p>
            `;
        } else {
            resultDiv.className = 'card mb-4';
            resultDiv.style.borderLeft = '4px solid #ef4444';
            resultDiv.innerHTML = `
                <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 1rem;">
                    <span style="font-size: 1.5rem;">❌</span>
                    <h3 style="margin: 0; color: #ef4444;">Ошибки компиляции</h3>
                </div>
                <div style="background: var(--bg-secondary); padding: 1rem; border-radius: 0.5rem; margin-bottom: 1rem;">
                    <pre style="margin: 0; color: #ef4444; font-size: 0.875rem;"><code>${result.compilation.errors.join('\n')}</code></pre>
                </div>
                ${result.hints && result.hints.length > 0 ? `
                    <div style="background: #fef3c7; padding: 1rem; border-radius: 0.5rem; border-left: 4px solid #f59e0b;">
                        <h4 style="margin: 0 0 0.5rem 0;">💡 Подсказки:</h4>
                        <ul style="margin: 0; padding-left: 1.5rem;">
                            ${result.hints.map(h => `<li>${h}</li>`).join('')}
                        </ul>
                    </div>
                ` : ''}
                <p class="text-secondary" style="font-size: 0.875rem; margin-top: 0.5rem;">
                    Попыток: ${result.attempts}
                </p>
            `;
        }
        
        showLoading(false);
        
    } catch (error) {
        showLoading(false);
        showNotification('Ошибка отправки решения', 'error');
    }
}

// Отправка Review задачи
async function submitReviewTask() {
    const foundIssuesText = document.getElementById('foundIssues').value;
    if (!foundIssuesText.trim()) {
        showNotification('Укажи найденные проблемы', 'error');
        return;
    }
    
    const foundIssues = foundIssuesText.split('\n').filter(line => line.trim());
    
    // Собираем ответы на вопросы
    const reviewAnswers = {};
    if (currentTask.review_questions) {
        currentTask.review_questions.forEach((q, idx) => {
            const answerEl = document.getElementById(`reviewAnswer_${idx}`);
            if (answerEl) {
                reviewAnswers[`q${idx + 1}`] = answerEl.value;
            }
        });
    }
    
    let improvedCode = null;
    if (improvedCodeEditor && improvedCodeEditor.getValue) {
        improvedCode = improvedCodeEditor.getValue();
    } else {
        const textarea = document.getElementById('improvedCodeTextarea');
        if (textarea) improvedCode = textarea.value;
    }
    
    try {
        showLoading(true);
        
        const response = await fetch(`/api/tasks/${currentTask.id}/submit`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                found_issues: foundIssues,
                review_answers: reviewAnswers,
                improved_code: improvedCode,
                time_spent: 0
            })
        });
        
        const result = await response.json();
        
        // Показываем результат
        const resultDiv = document.getElementById('reviewResult');
        resultDiv.classList.remove('hidden');
        
        if (result.success) {
            resultDiv.className = 'card mb-4';
            resultDiv.style.borderLeft = '4px solid #10b981';
            resultDiv.innerHTML = `
                <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 1rem;">
                    <span style="font-size: 1.5rem;">✅</span>
                    <h3 style="margin: 0; color: #10b981;">Отличный ревью!</h3>
                </div>
                <p>Ты нашел ${result.matched_issues.length} из ${result.expected_issues.length} проблем.</p>
                <p style="font-size: 1.25rem; font-weight: 600; color: var(--accent-color); margin: 1rem 0;">
                    Оценка: ${result.score}%
                </p>
                <div style="background: var(--bg-secondary); padding: 1rem; border-radius: 0.5rem; margin-top: 1rem;">
                    <p style="font-weight: 600; margin-bottom: 0.5rem;">${result.feedback}</p>
                </div>
            `;
        } else {
            resultDiv.className = 'card mb-4';
            resultDiv.style.borderLeft = '4px solid #f59e0b';
            resultDiv.innerHTML = `
                <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 1rem;">
                    <span style="font-size: 1.5rem;">⚠️</span>
                    <h3 style="margin: 0;">Можно лучше</h3>
                </div>
                <p>Ты нашел ${result.matched_issues.length} из ${result.expected_issues.length} проблем.</p>
                <p style="font-size: 1.25rem; font-weight: 600; color: #f59e0b; margin: 1rem 0;">
                    Оценка: ${result.score}%
                </p>
                <div style="background: var(--bg-secondary); padding: 1rem; border-radius: 0.5rem; margin-top: 1rem;">
                    <p style="font-weight: 600; margin-bottom: 0.5rem;">${result.feedback}</p>
                    <div style="margin-top: 1rem;">
                        <p style="font-weight: 600; margin-bottom: 0.5rem;">Ожидаемые проблемы:</p>
                        <ul style="margin-left: 1.5rem;">
                            ${result.expected_issues.map(issue => `<li>${issue}</li>`).join('')}
                        </ul>
                    </div>
                </div>
            `;
        }
        
        showLoading(false);
        
    } catch (error) {
        showLoading(false);
        showNotification('Ошибка отправки ревью', 'error');
    }
}

// Показать подсказки
function showHints() {
    if (!currentTask.hints || currentTask.hints.length === 0) {
        showNotification('Подсказки пока недоступны', 'info');
        return;
    }
    
    const hintsHtml = currentTask.hints.map((hint, idx) => `
        <div style="padding: 1rem; background: #fef3c7; border-radius: 0.5rem; margin-bottom: 0.5rem; border-left: 4px solid #f59e0b;">
            <strong>Подсказка ${idx + 1}:</strong> ${hint}
        </div>
    `).join('');
    
    document.getElementById('compilationResult').classList.remove('hidden');
    document.getElementById('compilationResult').className = 'card mb-4';
    document.getElementById('compilationResult').style.borderLeft = '4px solid #f59e0b';
    document.getElementById('compilationResult').innerHTML = `
        <h3 style="margin-bottom: 1rem;">💡 Подсказки</h3>
        ${hintsHtml}
    `;
}

// Утилиты
function parseMarkdownToHtml(text) {
    let html = text.replace(/```(\w+)?\n([\s\S]*?)```/g, (match, lang, code) => {
        return `<pre><code class="language-${lang || 'text'}">${escapeHtml(code.trim())}</code></pre>`;
    });
    html = html.replace(/`([^`]+)`/g, '<code>$1</code>');
    html = html.replace(/\n\n/g, '</p><p>');
    html = html.replace(/\n/g, '<br>');
    return '<p>' + html + '</p>';
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function showLoading(show) {
    document.getElementById('loadingSpinner').classList.toggle('hidden', !show);
}

// Добавляем стили для select
const style = document.createElement('style');
style.textContent = `
    .select-input {
        padding: 0.5rem 1rem;
        border: 1px solid var(--border-color);
        border-radius: 0.5rem;
        background: white;
        font-size: 0.875rem;
        cursor: pointer;
    }
    .select-input:hover {
        border-color: var(--accent-color);
    }
    .grid.grid-2 {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
        gap: 1.5rem;
    }
`;
document.head.appendChild(style);

