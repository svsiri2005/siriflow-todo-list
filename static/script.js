async function addTask() {
    const input = document.getElementById("taskInput");
    if (!input.value.trim()) return;

    await fetch('/add', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ content: input.value })
    });
    window.location.reload();
}

async function toggleTask(taskId) {
    await fetch(`/toggle/${taskId}`, { method: 'POST' });
    window.location.reload();
}

async function clearList() {
    if (confirm("Clear all today's tasks?")) {
        await fetch('/clear', { method: 'POST' });
        window.location.reload();
    }
}