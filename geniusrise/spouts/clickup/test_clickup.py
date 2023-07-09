from geniusrise.data_sources.project_management.clickup import ClickUpDataFetcher


def test_fetch_workspaces():
    fetcher = ClickUpDataFetcher()
    workspaces = fetcher.fetch_workspaces()
    assert isinstance(workspaces, list)
    for workspace in workspaces:
        assert "Workspace Name:" in workspace
        assert "Workspace ID:" in workspace


def test_fetch_spaces():
    fetcher = ClickUpDataFetcher()
    # replace 'team_id' with an actual team ID from your ClickUp account
    spaces = fetcher.fetch_spaces("team_id")
    assert isinstance(spaces, list)
    for space in spaces:
        assert "Space Name:" in space
        assert "Space ID:" in space


def test_fetch_folders():
    fetcher = ClickUpDataFetcher()
    # replace 'space_id' with an actual space ID from your ClickUp account
    folders = fetcher.fetch_folders("space_id")
    assert isinstance(folders, list)
    for folder in folders:
        assert "Folder Name:" in folder
        assert "Folder ID:" in folder


def test_fetch_lists():
    fetcher = ClickUpDataFetcher()
    # replace 'folder_id' with an actual folder ID from your ClickUp account
    lists = fetcher.fetch_lists("folder_id")
    assert isinstance(lists, list)
    for entry in lists:
        assert "List Name:" in entry
        assert "List ID:" in entry


def test_fetch_tasks():
    fetcher = ClickUpDataFetcher()
    # replace 'list_id' with an actual list ID from your ClickUp account
    tasks = fetcher.fetch_tasks("list_id")
    assert isinstance(tasks, list)
    for task in tasks:
        assert "Task Name:" in task
        assert "Task ID:" in task
        assert "Task Status:" in task


def test_fetch_subtasks():
    fetcher = ClickUpDataFetcher()
    # replace 'task_id' with an actual task ID from your ClickUp account
    subtasks = fetcher.fetch_subtasks("task_id")
    assert isinstance(subtasks, list)
    for subtask in subtasks:
        assert "Subtask Name:" in subtask
        assert "Subtask ID:" in subtask
        assert "Subtask Status:" in subtask


def test_fetch_checklists():
    fetcher = ClickUpDataFetcher()
    # replace 'task_id' with an actual task ID from your ClickUp account
    checklists = fetcher.fetch_checklists("task_id")
    assert isinstance(checklists, list)
    for checklist in checklists:
        assert "Checklist Name:" in checklist
        assert "Checklist ID:" in checklist


def test_fetch_custom_fields():
    fetcher = ClickUpDataFetcher()
    # replace 'list_id' with an actual list ID from your ClickUp account
    custom_fields = fetcher.fetch_custom_fields("list_id")
    assert isinstance(custom_fields, list)
    for field in custom_fields:
        assert "Custom Field Name:" in field
        assert "CustomField ID:" in field


def test_fetch_comments():
    fetcher = ClickUpDataFetcher()
    # replace 'task_id' with an actual task ID from your ClickUp account
    comments = fetcher.fetch_comments("task_id")
    assert isinstance(comments, list)
    for comment in comments:
        assert "Comment ID:" in comment
        assert "Comment Text:" in comment


def test_fetch_attachments():
    fetcher = ClickUpDataFetcher()
    # replace 'task_id' with an actual task ID from your ClickUp account
    attachments = fetcher.fetch_attachments("task_id")
    assert isinstance(attachments, list)
    for attachment in attachments:
        assert "Attachment ID:" in attachment
        assert "Attachment Filename:" in attachment


def test_fetch_all_data():
    fetcher = ClickUpDataFetcher()
    # replace 'team_id' with an actual team ID from your ClickUp account
    all_data = fetcher.fetch_all_data("team_id")
    assert isinstance(all_data, list)
    for data in all_data:
        assert "Space:" in data
        assert "Folder:" in data
        assert "List:" in data
        assert "Task:" in data
        assert "Subtasks:" in data
        assert "Checklists:" in data
        assert "Comments:" in data
        assert "Attachments:" in data
