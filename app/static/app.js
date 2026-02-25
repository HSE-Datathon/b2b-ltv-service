const out = document.getElementById("output");
const dashContainer = document.getElementById("dash_container");

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
        dashContainer.textContent = "Ошибка загрузки дешборда: " + e;
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
