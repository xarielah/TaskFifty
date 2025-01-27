from prettytable import from_db_cursor
from services.db_service import db_instance
from lib.utils import get_prompt, update_status_if_late
from lib.enums import Priority, Status, Column


def view_tasks():
    update_status_if_late()
    db_instance().cursor.execute(
        """
        SELECT
            id,
            title,
            description,
        strftime('%H:%M, %d-%m-%Y', deadline, 'unixepoch', 'localtime') as deadline,
        CASE priority
            WHEN 1 THEN 'LOW'
            WHEN 2 THEN 'MEDIUM'
            WHEN 3 THEN 'HIGH'
            ELSE 'UNKNOWN'
        END AS priority,
        CASE status
            WHEN 1 THEN 'TODO'
            WHEN 2 THEN 'DONE'
            WHEN 3 THEN 'LATE'
            ELSE 'UNKNOWN'
        END AS status,
        strftime('%H:%M:%S, %d-%m-%Y', created, 'unixepoch', 'localtime') as created,
        strftime('%H:%M:%S, %d-%m-%Y', updated, 'unixepoch', 'localtime') as updated
        FROM tasks"""
    )
    pretty_formatted_table = from_db_cursor(db_instance().cursor)
    print("\n", pretty_formatted_table, sep="")


def add_task():
    title = get_prompt("title", "\nPlease choose a title: ")
    description = get_prompt("description", "\nPlease describe your task: ")
    deadline = get_prompt(
        "deadline",
        "\nPlease enter a date in the future,\n"
        + "formatted as follows:\nhh:mm dd-mm-yy\n",
    )
    priority = get_prompt(
        "priority",
        "\nPlease choose the priority:\n\n"
        + "\n".join(f"{p.value}. {p.name}" for p in Priority)
        + "\n\nYour choice: ",
    )
    status = Status.TODO.value

    try:
        db_instance().cursor.execute(
            """INSERT INTO tasks 
                    (title, description, deadline, priority, status, created, updated) 
                VALUES 
                    (?, ?, ?, ?, ?, strftime('%s', 'now'), strftime('%s', 'now'))
                    """,
            (title, description, deadline, priority, status),
        )
    except:
        db_instance().conn.rollback()


def delete_task():
    view_tasks()
    id_to_delete = get_prompt(
        "task id", "\nPlease type the id of the task you wish to delete: "
    )
    db_instance().cursor.execute("DELETE FROM tasks WHERE id = ?", str(id_to_delete))


def update_task():
    view_tasks()

    id_to_update = get_prompt(
        "task id", "\nPlease type the id of the task you wish to update: "
    )

    chosen_column = get_prompt(
        "column",
        "\nPlease choose a column:\n\n"
        + "\n".join(f"{c.value}. {c.name.title()}" for c in Column)
        + "\n\nYour choice: ",
    )

    chosen_column_name = Column(chosen_column).name.lower()

    updated_column = get_prompt(
        chosen_column_name, f"\nEnter the new {chosen_column_name}: "
    )

    try:
        db_instance().cursor.execute(
            f"""UPDATE tasks
                SET {chosen_column_name} = ?, updated = strftime('%s', 'now')
                WHERE id = ?;""",
            (updated_column, id_to_update),
        )
        return

    except:
        print("ERROR")
        db_instance().conn.rollback()
