"""Command-line interface for the task manager."""
import argparse
import logging

from task_manager.tasks import add_task, complete_task, list_tasks


def main(argv: list[str] | None = None) -> None:
    """Run the task manager CLI with the given arguments (defaults to sys.argv)."""
    logging.basicConfig(level=logging.WARNING, format="%(levelname)s: %(message)s")

    parser = argparse.ArgumentParser(description="Simple task manager")
    subparsers = parser.add_subparsers(dest="command", required=True)

    add_parser = subparsers.add_parser("add", help="Add a task")
    add_parser.add_argument("title")

    done_parser = subparsers.add_parser("done", help="Complete a task")
    done_parser.add_argument("task_id", type=int)

    subparsers.add_parser("list", help="List all tasks")

    args = parser.parse_args(argv)

    if args.command == "add":
        task = add_task(args.title)
        print(f"Added task #{task['id']}: {task['title']}")
    elif args.command == "done":
        if complete_task(args.task_id):
            print(f"Task #{args.task_id} marked done")
        else:
            print(f"Task #{args.task_id} not found")
    elif args.command == "list":
        for task in list_tasks():
            status = "x" if task["done"] else " "
            print(f"[{status}] #{task['id']} {task['title']}")


if __name__ == "__main__":
    main()
