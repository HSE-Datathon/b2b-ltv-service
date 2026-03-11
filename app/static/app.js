const out = document.getElementById("output");
const dashContainer = document.getElementById("dash_container");

let allCompanies = [];

function renderSelect(selectEl, companies) {
    selectEl.innerHTML = companies
        .slice(0, 200)
        .map((c) => `<option value="${c.company_id}">${c.company_id} · ${c.ltv_segment} · ${Math.round(c.predicted_ltv).toLocaleString("ru")} ₽</option>`)
        .join("");
}

function setupPicker(searchId, selectId, countId) {
    const searchEl = document.getElementById(searchId);
    const selectEl = document.getElementById(selectId);
    const countEl = document.getElementById(countId);

    searchEl.addEventListener("input", () => {
        const q = searchEl.value.trim().toLowerCase();
        const filtered = q
            ? allCompanies.filter((c) => c.company_id.includes(q) || c.ltv_segment.includes(q))
            : allCompanies;
        countEl.textContent = `(${filtered.length})`;
        renderSelect(selectEl, filtered);
    });
}

async function loadCompanies() {
    try {
        const res = await fetch("/companies");
        allCompanies = await res.json();

        ["ltv", "nbo"].forEach((prefix) => {
            const countEl = document.getElementById(`${prefix}_company_count`);
            if (countEl) countEl.textContent = `(${allCompanies.length})`;
            renderSelect(document.getElementById(`${prefix}_company_id`), allCompanies);
            setupPicker(`${prefix}_search`, `${prefix}_company_id`, `${prefix}_company_count`);
        });
    } catch (e) {
        console.warn("Не удалось загрузить список компаний:", e);
    }
}

loadCompanies();

function showOutputTab() {
    document.querySelectorAll(".tab").forEach((t) => t.classList.remove("active"));
    document.querySelectorAll(".tab-panel").forEach((p) => p.classList.remove("active"));
    document.querySelector('.tab[data-tab="output"]').classList.add("active");
    document.getElementById("panel-output").classList.add("active");
}

async function callLtv() {
    const btn = document.getElementById("ltv_btn");
    btn.disabled = true;
    out.textContent = "Запрос к /ltv/predict…";
    try {
        const body = {
            company_id: document.getElementById("ltv_company_id").value || null,
            company_size: document.getElementById("ltv_company_size").value
                ? Number(document.getElementById("ltv_company_size").value)
                : null,
            revenue: document.getElementById("ltv_revenue").value
                ? Number(document.getElementById("ltv_revenue").value)
                : null
        };
        const res = await fetch("/ltv/predict", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(body)
        });
        const data = await res.json();
        out.textContent = JSON.stringify(data, null, 2);
        showOutputTab();
    } catch (e) {
        out.textContent = "Ошибка запроса: " + e;
        showOutputTab();
    } finally {
        btn.disabled = false;
    }
}

async function callNbo() {
    const btn = document.getElementById("nbo_btn");
    btn.disabled = true;
    out.textContent = "Запрос к /nbo/recommend…";
    try {
        const body = {
            company_id: document.getElementById("nbo_company_id").value || null,
            top_k: document.getElementById("nbo_top_k").value
                ? Number(document.getElementById("nbo_top_k").value)
                : 5
        };
        const res = await fetch("/nbo/recommend", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(body)
        });
        const data = await res.json();
        out.textContent = JSON.stringify(data, null, 2);
        showOutputTab();
    } catch (e) {
        out.textContent = "Ошибка запроса: " + e;
        showOutputTab();
    } finally {
        btn.disabled = false;
    }
}

async function loadDashboard() {
    const btn = document.getElementById("dash_btn");
    if (!btn || !dashContainer) return;
    btn.disabled = true;
    dashContainer.textContent = "Загружаем данные из /ltv/segments…";
    try {
        const res = await fetch("/ltv/segments");
        const data = await res.json();
        if (!Array.isArray(data) || data.length === 0) {
            dashContainer.textContent = "Данные по сегментам LTV пока отсутствуют.";
            return;
        }
        const rows = data
            .map(
                (s) =>
                    `<tr><td>${s.ltv_segment}</td><td>${s.avg_ltv}</td><td>${s.clients_count}</td></tr>`
            )
            .join("");
        dashContainer.innerHTML = `
            <table>
                <thead>
                    <tr>
                        <th>LTV сегмент</th>
                        <th>Средний LTV</th>
                        <th>Клиентов</th>
                    </tr>
                </thead>
                <tbody>${rows}</tbody>
            </table>
        `;
    } catch (e) {
        dashContainer.textContent = "Ошибка загрузки дашборда: " + e;
    } finally {
        btn.disabled = false;
    }
}

document.getElementById("ltv_btn").addEventListener("click", callLtv);
document.getElementById("nbo_btn").addEventListener("click", callNbo);
document.getElementById("dash_btn").addEventListener("click", loadDashboard);

document.querySelectorAll(".tab").forEach((tab) => {
    tab.addEventListener("click", () => {
        const targetId = "panel-" + tab.getAttribute("data-tab");
        document.querySelectorAll(".tab").forEach((t) => t.classList.remove("active"));
        document.querySelectorAll(".tab-panel").forEach((p) => p.classList.remove("active"));
        tab.classList.add("active");
        const panel = document.getElementById(targetId);
        if (panel) panel.classList.add("active");
    });
});
