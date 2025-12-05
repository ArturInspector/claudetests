// Утилиты для работы с API

const API = {
    async getTopics() {
        const response = await fetch('/api/topics');
        return response.json();
    },
    
    async getQuestion(topicId, difficulty = null, sessionId = null) {
        let url = `/api/question/${topicId}`;
        const params = new URLSearchParams();
        
        if (difficulty) params.append('difficulty', difficulty);
        if (sessionId) params.append('session_id', sessionId);
        
        if (params.toString()) url += `?${params.toString()}`;
        
        const response = await fetch(url);
        if (!response.ok) {
            throw new Error('Не удалось загрузить вопрос');
        }
        return response.json();
    },
    
    async getQuestionWithAnswer(questionId) {
        const response = await fetch(`/api/question/${questionId}/answer`);
        return response.json();
    },
    
    async submitAnswer(questionId, userAnswer, sessionId = null, timeSpent = null, showedAnswer = false, confidenceLevel = null) {
        const response = await fetch('/api/answer', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                question_id: questionId,
                user_answer: userAnswer,
                session_id: sessionId,
                time_spent: timeSpent,
                showed_answer: showedAnswer,
                confidence_level: confidenceLevel
            })
        });
        return response.json();
    },
    
    async startSession() {
        const response = await fetch('/api/session/start', {
            method: 'POST'
        });
        return response.json();
    },
    
    async endSession(sessionId) {
        const response = await fetch('/api/session/end', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                session_id: sessionId
            })
        });
        return response.json();
    },
    
    async getStats() {
        const response = await fetch('/api/stats');
        return response.json();
    },
    
    async getRecentSessions(limit = 10) {
        const response = await fetch(`/api/sessions/recent?limit=${limit}`);
        return response.json();
    },
    
    async importQuestions(file) {
        const formData = new FormData();
        formData.append('file', file);
        
        const response = await fetch('/api/import', {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Ошибка импорта');
        }
        
        return response.json();
    },
    
    // Tasks API
    async getTasks(filters = {}) {
        const params = new URLSearchParams();
        if (filters.block) params.append('block', filters.block);
        if (filters.language) params.append('language', filters.language);
        if (filters.difficulty) params.append('difficulty', filters.difficulty);
        if (filters.task_type) params.append('task_type', filters.task_type);
        
        const response = await fetch(`/api/tasks?${params.toString()}`);
        return response.json();
    },
    
    async getTask(taskId) {
        const response = await fetch(`/api/tasks/${taskId}`);
        return response.json();
    },
    
    async submitTask(taskId, data) {
        const response = await fetch(`/api/tasks/${taskId}/submit`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        return response.json();
    },
    
    async importTasks(file) {
        const formData = new FormData();
        formData.append('file', file);
        
        const response = await fetch('/api/tasks/import', {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Ошибка импорта');
        }
        
        return response.json();
    }
};

const Utils = {
    formatDate(dateString) {
        const date = new Date(dateString);
        return date.toLocaleDateString('ru-RU', {
            year: 'numeric',
            month: 'long',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    },
    
    formatDuration(minutes) {
        if (minutes < 1) return 'меньше минуты';
        if (minutes < 60) return `${Math.round(minutes)} мин`;
        
        const hours = Math.floor(minutes / 60);
        const mins = Math.round(minutes % 60);
        return `${hours} ч ${mins} мин`;
    },
    
    getDifficultyClass(difficulty) {
        const classes = {
            'Easy': 'difficulty-easy',
            'Medium': 'difficulty-medium',
            'Hard': 'difficulty-hard'
        };
        return classes[difficulty] || 'difficulty-medium';
    },
    
    // Сохранение в localStorage
    saveSession(sessionId) {
        localStorage.setItem('currentSession', sessionId);
    },
    
    getSession() {
        return localStorage.getItem('currentSession');
    },
    
    clearSession() {
        localStorage.removeItem('currentSession');
    },
    
    highlightCode(code, language) {
        return code;
    },
    
    parseMarkdown(text) {
        let html = text.replace(/```(\w+)?\n([\s\S]*?)```/g, (match, lang, code) => {
            return `<pre><code class="language-${lang || 'text'}">${escapeHtml(code.trim())}</code></pre>`;
        });
        
        html = html.replace(/`([^`]+)`/g, '<code>$1</code>');
        
        // Новые строки
        html = html.replace(/\n/g, '<br>');
        
        return html;
    }
};

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Копирование в буфер обмена
async function copyToClipboard(text) {
    try {
        await navigator.clipboard.writeText(text);
        return true;
    } catch (err) {
        // Fallback для старых браузеров
        const textarea = document.createElement('textarea');
        textarea.value = text;
        textarea.style.position = 'fixed';
        textarea.style.opacity = '0';
        document.body.appendChild(textarea);
        textarea.select();
        const success = document.execCommand('copy');
        document.body.removeChild(textarea);
        return success;
    }
}

// Уведомления
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    
    // Иконки для разных типов
    const icons = {
        success: '✓',
        error: '✕',
        info: 'ℹ'
    };
    
    const colors = {
        success: { bg: '#059669', border: '#047857' },
        error: { bg: '#dc2626', border: '#b91c1c' },
        info: { bg: '#c17e5e', border: '#a96b4d' }
    };
    
    const color = colors[type] || colors.info;
    
    notification.innerHTML = `
        <span style="font-weight: 600; margin-right: 0.5rem;">${icons[type] || icons.info}</span>
        <span>${message}</span>
    `;
    
    notification.style.cssText = `
        position: fixed;
        top: 24px;
        right: 24px;
        padding: 1rem 1.5rem;
        background: ${color.bg};
        color: white;
        border-radius: 0.75rem;
        border: 1px solid ${color.border};
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.2), 0 4px 6px -4px rgba(0, 0, 0, 0.1);
        z-index: 1000;
        animation: slideIn 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        display: flex;
        align-items: center;
        font-size: 0.9375rem;
        max-width: 400px;
    `;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s cubic-bezier(0.4, 0, 0.2, 1)';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

// Добавляем стили для анимации
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    
    @keyframes slideOut {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(100%);
            opacity: 0;
        }
    }
`;
document.head.appendChild(style);

