import git
from flexmock import flexmock

from packit import local_project
from packit.local_project import LocalProject


def test_local_project_full_name():
    project = LocalProject(full_name="namespace/repository_name")
    assert project.repo_name == "repository_name"
    assert project.namespace == "namespace"
    assert project.full_name == "namespace/repository_name"


def test_local_project_repo_namespace():
    project = LocalProject(repo_name="repository_name", namespace="namespace")
    assert project.repo_name == "repository_name"
    assert project.namespace == "namespace"
    assert project.full_name == "namespace/repository_name"


def test_local_project_working_dir_project():
    """Get git_url, namespace/repo and service from git_project"""
    project_mock = flexmock(
        repo="repository_name",
        namespace="namespace",
        service=flexmock(),
        get_git_urls=lambda: {"git": "ssh url"},
    )

    project = LocalProject(
        git_project=project_mock,
        working_dir=flexmock(),
        git_repo=flexmock(active_branch="branch"),
    )
    assert project.git_service
    assert project.git_project
    assert project.repo_name == "repository_name"
    assert project.namespace == "namespace"
    assert project.full_name == "namespace/repository_name"


def test_local_project_repo_url():
    """Get working_dir from git_repo"""
    project = LocalProject(
        git_repo=flexmock(active_branch="branch", working_dir="something"),
        git_url=flexmock(),
    )
    assert project.git_repo
    assert project.working_dir == "something"
    assert project._branch == "branch"


def test_local_project_repo():
    """Get git_url from git_repo"""
    project = LocalProject(
        git_repo=flexmock(active_branch="branch", working_dir="something")
        .should_receive("remote")
        .replace_with(lambda: flexmock(urls=["git/url"]))
        .once()
        .mock()
    )
    assert project.git_repo
    assert project.working_dir == "something"
    assert project._branch == "branch"
    assert project.git_url == "git/url"


def test_clone_project_checkout_branch():
    """Checkout existing branch"""
    project = LocalProject(
        git_repo=flexmock(
            active_branch="branch",
            working_dir="something",
            branches={
                "other": flexmock(checkout=lambda: None)
                .should_receive("checkout")
                .once()
                .mock()
            },
        ),
        branch="other",
        git_url=flexmock(),
    )
    assert project.git_repo
    assert project.working_dir == "something"
    assert project._branch == "other"


def test_clone_project_checkout_new_branch():
    """Checkout newly created branch"""
    branches = {}
    project = LocalProject(
        git_repo=flexmock(
            active_branch="branch", working_dir="something", branches=branches
        )
        .should_receive("create_head")
        .with_args("other")
        .replace_with(
            lambda x: branches.setdefault(
                x, flexmock().should_receive("checkout").once().mock()
            )
        )
        .once()
        .mock(),
        branch="other",
        git_url=flexmock(),
    )
    assert project.git_repo
    assert project.working_dir == "something"
    assert project._branch == "other"


def test_clone_project_service_repo_namespace():
    """Get git_project from git_service and namespace/repo"""
    project = LocalProject(
        repo_name="repo",
        namespace="namespace",
        git_service=flexmock()
        .should_receive("get_project")
        .with_args(repo="repo", namespace="namespace")
        .replace_with(lambda repo, namespace: flexmock())
        .mock(),
        git_url=flexmock(),
        working_dir=flexmock(),
        git_repo=flexmock(active_branch=flexmock()),
    )
    assert project.repo_name
    assert project.namespace
    assert project.git_service
    assert project.git_project


def test_local_project_clone():
    flexmock(local_project).should_receive("get_repo").with_args(
        "http://some.example/url"
    ).and_return(flexmock(working_dir="some/example/path", active_branch="branch"))

    project = LocalProject(git_url="http://some.example/url")

    assert project.git_url
    assert project.git_repo
    assert project.branch == "branch"
    assert project.working_dir_temporary

    project.working_dir_temporary = False


def test_local_project_repo_from_working_dir():
    flexmock(local_project).should_receive("is_git_repo").with_args(
        "some/example/path"
    ).and_return(True)
    flexmock(
        git,
        Repo=flexmock(
            active_branch="branch", remote=lambda: flexmock(urls=["git/url"])
        ),
    )
    project = LocalProject(working_dir="some/example/path")

    assert project.git_url == "git/url"
    assert project.git_repo
    assert project.git_repo.active_branch == "branch"
    assert project.branch == "branch"
    assert not project.working_dir_temporary


def test_local_project_dir_url():

    flexmock(local_project).should_receive("get_repo").with_args(
        "http://some.example/url", "some/example/path"
    ).and_return(flexmock(working_dir="some/example/path", active_branch="branch"))

    project = LocalProject(
        git_url="http://some.example/url", working_dir="some/example/path"
    )

    assert project.git_url == "http://some.example/url"
    assert project.git_repo
    assert project.branch == "branch"
    assert project.git_repo.active_branch == "branch"
    assert project.git_repo.working_dir == "some/example/path"
    assert not project.working_dir_temporary
