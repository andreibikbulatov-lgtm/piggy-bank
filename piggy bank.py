import json
from datetime import datetime, timedelta

class Goal:
    def __init__(self, title, target, category):
        self.title = title.strip()
        self.target_amount = float(target)
        self.current_balance = 0.0
        self.category = category or "Разное"
        self.status = "Новая"
        self.due_date = None

    def to_dict(self):
        return self.__dict__

    @staticmethod
    def from_dict(d):
        g = Goal(d["title"], d["target_amount"], d.get("category"))
        g.current_balance = d.get("current_balance", 0.0)
        g.status = d.get("status", "Новая")
        g.due_date = d.get("due_date")
        return g

    def update_balance(self, amount):
        try:
            amount = float(amount)
            if not (amount == amount) or abs(amount) == float('inf'):
                return
            self.current_balance = max(0.0, self.current_balance + amount)
            self.status = "Выполнена" if self.current_balance >= self.target_amount else "В работе"
        except (TypeError, ValueError):
            pass

    def progress(self):
        if self.target_amount <= 0:
            return 0.0
        return (self.current_balance / self.target_amount) * 100


def load_goals(filename):
    try:
        with open(filename, "r", encoding="utf-8") as f:
            data = json.load(f)
            if not isinstance(data, list):
                return []
            goals = []
            for item in data:
                if not isinstance(item, dict):
                    continue
                if "title" not in item or "target_amount" not in item:
                    continue
                try:
                    g = Goal.from_dict(item)
                    if g.target_amount > 0 and g.title:
                        goals.append(g)
                except Exception:
                    continue
            return goals
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def save_goals(goals, filename):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump([g.to_dict() for g in goals], f, ensure_ascii=False, indent=2)


def validate_date(date_str):
    if not date_str:
        return False
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return True
    except ValueError:
        return False


def show_dashboard(goals):
    print("\n" + "=" * 50)
    print("  КОПИЛКА — текущий прогресс")
    print("=" * 50)
    if not goals:
        print("  Целей пока нет.")
    else:
        for i, g in enumerate(goals):
            bar_len = 20
            filled = int(g.progress() / 100 * bar_len)
            bar = "█" * filled + "░" * (bar_len - filled)
            print(f"  {i+1}. {g.title} [{g.category}]")
            print(f"     {bar} {g.progress():.0f}%  {g.current_balance:.0f}/{g.target_amount:.0f} [{g.status}]")
        total_bal = sum(g.current_balance for g in goals)
        total_tgt = sum(g.target_amount for g in goals)
        overall = (total_bal / total_tgt * 100) if total_tgt else 0.0
        print(f"  ── Общий прогресс: {overall:.1f}% ──")
    print("=" * 50)


def check_reminders(goals):
    today = datetime.now().strftime("%Y-%m-%d")
    for g in goals:
        if g.due_date and validate_date(g.due_date) and g.due_date <= today and g.status != "Выполнена":
            print(f"⏰ Срок по цели '{g.title}' наступил ({g.due_date})!")


def select_goal(goals, prompt):
    if not goals:
        print("Список пуст.")
        return None
    for i, g in enumerate(goals):
        print(f"{i+1}. {g.title} — {g.current_balance:.0f}/{g.target_amount:.0f} ({g.progress():.0f}%) [{g.status}]")
    raw = input(prompt).strip()
    if raw == "0":
        return "cancel"
    try:
        idx = int(raw) - 1
        return idx if 0 <= idx < len(goals) else None
    except ValueError:
        return None


def get_number(prompt, allow_zero_cancel=True):
    while True:
        raw = input(prompt).strip()
        if allow_zero_cancel and raw == "0":
            return "0"
        try:
            val = float(raw)
            if val <= 0 and not allow_zero_cancel:
                print("Значение должно быть больше 0.")
                continue
            if abs(val) == float('inf') or val != val:
                print("Недопустимое число.")
                continue
            return val
        except ValueError:
            print("Введите корректное число.")


def suggest_due_date(goal):
    remaining = goal.target_amount - goal.current_balance
    if remaining <= 0:
        return None
    print(f"\nОсталось накопить: {remaining:.0f}")
    print("Частота пополнений: 1 — неделя, 2 — две недели, 3 — месяц, 0 — отмена")
    freq = input("Выберите частоту (1/2/3/0): ").strip()
    if freq == "0":
        return "cancel"
    deposit = get_number("Сумма пополнения (0 — отмена): ", allow_zero_cancel=True)
    if deposit == "0":
        return "cancel"
    days_per_period = {"1": 7, "2": 14, "3": 30}
    days = int((remaining / deposit) * days_per_period.get(freq, 30))
    return (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d")


def main():
    filename = "data.json"
    goals = load_goals(filename)

    while True:
        show_dashboard(goals)
        check_reminders(goals)

        print("\n1. Добавить цель | 2. Изменить баланс | 3. Подробный прогресс")
        print("4. Напоминание | 5. Удалить цель | 6. Выход")
        choice = input("Действие (1-6): ").strip()

        if choice == "1":
            title = input("Название (0 — отмена): ").strip()
            if title == "0" or not title.strip():
                print("Отмена.")
                continue
            target = get_number("Итоговая сумма (0 — отмена): ")
            if target == "0":
                print("Отмена.")
                continue
            category = input("Категория (пусто → Разное, 0 — отмена): ").strip()
            if category == "0":
                print("Отмена.")
                continue
            goals.append(Goal(title, target, category))
            save_goals(goals, filename)
            print(f"Цель '{title}' добавлена.")

        elif choice == "2":
            idx = select_goal(goals, "Номер цели (0 — отмена): ")
            if idx is None or idx == "cancel":
                print("Отмена." if idx == "cancel" else "")
                continue
            raw = input("Сумма (+пополнить, -списать, 0 — отмена): ").strip()
            if raw == "0":
                print("Отмена.")
                continue
            goals[idx].update_balance(raw)
            save_goals(goals, filename)
            print(f"Баланс: {goals[idx].current_balance:.2f} [{goals[idx].status}]")

        elif choice == "3":
            if not goals:
                print("Список пуст.")
            else:
                for g in goals:
                    print(f"- {g.title} [{g.category}] — {g.progress():.1f}% [{g.status}]")
                total_bal = sum(g.current_balance for g in goals)
                total_tgt = sum(g.target_amount for g in goals)
                overall = (total_bal / total_tgt * 100) if total_tgt else 0.0
                print(f"\nОбщий прогресс: {overall:.1f}%")
            input("\nНажмите Enter для возврата в меню...")

        elif choice == "4":
            idx = select_goal(goals, "Номер цели (0 — отмена): ")
            if idx is None or idx == "cancel":
                print("Отмена." if idx == "cancel" else "")
                continue
            if goals[idx].status == "Выполнена":
                print("Цель уже выполнена.")
                continue
            suggested = suggest_due_date(goals[idx])
            if suggested in (None, "cancel"):
                continue
            print(f"Рекомендуемая дата: {suggested}")
            ans = input("Использовать? (да/нет/0-отмена): ").strip().lower()
            if ans == "0":
                print("Отмена.")
                continue
            if ans == "да":
                goals[idx].due_date = suggested
            else:
                while True:
                    raw = input("Дата (ГГГГ-ММ-ДД, 0 — отмена): ").strip()
                    if raw == "0":
                        print("Отмена.")
                        break
                    if validate_date(raw):
                        goals[idx].due_date = raw
                        break
                    print("Некорректный формат даты. Используйте ГГГГ-ММ-ДД.")
                else:
                    continue
            save_goals(goals, filename)
            print(f"Напоминание: {goals[idx].title} → {goals[idx].due_date}")

        elif choice == "5":
            idx = select_goal(goals, "Номер цели (0 — отмена): ")
            if idx is None or idx == "cancel":
                print("Отмена." if idx == "cancel" else "")
                continue
            removed = goals.pop(idx)
            save_goals(goals, filename)
            print(f"Удалено: {removed.title}")

        elif choice == "6":
            print("До свидания!")
            break
        else:
            print("Неверный выбор. Введите число от 1 до 6.")


if __name__ == "__main__":
    main()
