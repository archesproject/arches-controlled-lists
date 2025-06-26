# Welcome to Arches Controlled Lists!

Arches Controlled Lists is an Arches application designed to manage controlled lists and reference data within the Arches platform.

Please see the [project page](http://archesproject.org/) for more information on the Arches project.


## Installation

If you are installing Arches Controlled Lists for the first time, you can install it as an Arches application into a project or run it directly as an Arches project. Running Arches Controlled Lists as a project can provide some convienience if you are a developer contributing to the Arches Controlled Lists project. Otherwise, **we strongly recommend running Arches Controlled Lists as an Arches Application** within a project because that will allow greater flexibility in customizing your project without the risk of conflicts when upgrading to the next version of Arches Controlled Lists.  

Install Arches Controlled Lists using the following command:
```
pip install arches-controlled-lists
```

For developer install instructions, see the [Developer Setup](#developer-setup-for-contributing-to-the-arches-controlled-lists-project) section below.


## Project Configuration

1. If you don't already have an Arches project, you'll need to create one by following the instructions in the Arches [documentation](http://archesproject.org/documentation/).

2. When your project is ready, add "arches_component_lab", "arches_controlled_lists", and "pgtrigger" to INSTALLED_APPS **below** the name of your project:
    ```
    INSTALLED_APPS = (
        ...
        "my_project_name",
        "arches_component_lab",
        "arches_controlled_lists",
        "pgtrigger",
    )
    ```

3. Make sure the following settings are added to your project
    ```
    REFERENCES_INDEX_NAME = "references"
    ELASTICSEARCH_CUSTOM_INDEXES = [
        {
            "module": "arches_controlled_lists.search_indexes.reference_index.ReferenceIndex",
            "name": REFERENCES_INDEX_NAME,
            "should_update_asynchronously": True,
        }
    ]
    TERM_SEARCH_TYPES = [
        {
            "type": "term",
            "label": _("Term Matches"),
            "key": "terms",
            "module": "arches.app.search.search_term.TermSearch",
        },
        {
            "type": "concept",
            "label": _("Concepts"),
            "key": "concepts",
            "module": "arches.app.search.concept_search.ConceptSearch",
        },
        {
            "type": "reference",
            "label": _("References"),
            "key": REFERENCES_INDEX_NAME,
            "module": "arches_controlled_lists.search_indexes.reference_index.ReferenceIndex",
        },
    ]

    ES_MAPPING_MODIFIER_CLASSES = [
        "arches_controlled_lists.search.references_es_mapping_modifier.ReferencesEsMappingModifier"
    ]
    ```

4. Next ensure arches and arches_controlled_lists are included as dependencies in package.json
    ```
    "dependencies": {
        "@uppy/aws-s3": "3.6.2",
        "@uppy/core": "3.13.0",
        "@uppy/dashboard": "3.9.0",
        "@uppy/drag-drop": "3.1.0",
        "@uppy/progress-bar": "3.1.1",
        "@uppy/companion-client": "3.1.3",
        "typescript": "5.6.2",
        "arches": "archesproject/arches#dev/8.0.x",
        "arches_controlled_lists": "archesproject/arches-controlled_lists#dev/1.0.x"
    }
    ```

5. Update urls.py to include the arches_controlled_lists and arches_component_lab urls
    ```
    urlpatterns = [
        path("", include("arches_controlled_lists.urls")),
        path("", include("arches_component_lab.urls")),
    ] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    ```

6. Run the arches application migrations (models and other data)
    ```
    python manage.py migrate arches_controlled_lists
    ```

7. Start your project
    ```
    python manage.py runserver
    ```

8. Next cd into your project's app directory (the one with package.json) install and build front-end dependencies:
    ```
    npm install
    npm run build_development
    ```

## Developer Setup (for contributing to the Arches Controlled Lists project)

1. Download the arches-controlled-lists repo:

    a.  If using the [Github CLI](https://cli.github.com/): `gh repo clone archesproject/arches-controlled-lists`
    
    b.  If not using the Github CLI: `git clone https://github.com/archesproject/arches-controlled-lists.git`

2. Download the arches package:

    a.  If using the [Github CLI](https://cli.github.com/): `gh repo clone archesproject/arches`

    b.  If not using the Github CLI: `git clone https://github.com/archesproject/arches.git`

3. Create a virtual environment outside of both repositories: 
    ```
    python3 -m venv ENV
    ```

4. Activate the virtual enviroment in your terminal:
    ```
    source ENV/bin/activate
    ```

5. Navigate to the `arches-controlled-lists` directory, and install the project (with development dependencies):
    ```
    cd arches-controlled-lists
    pip install -e '.[dev]'
    ```

6. Also install core arches for local development:
    ```
    pip install -e ../arches
    ```

1. Create a settings_local.py file with `DEBUG=True`:
    ```
    echo "DEBUG = True" > arches_controlled_lists/settings_local.py
    ```

7. Run the Django server:
    ```
    python manage.py runserver
    ```

8. **OPEN A NEW TERMINAL WINDOW**, the following step will take place in a new terminal window while the python server is running.

9. Ensure this new terminal window has the virtual environment activated.
    ```
    source ENV/bin/activate
    ```

10. (From the `arches-controlled-lists` top-level directory) install the frontend dependencies:
    ```
    npm install
    ```

11. Once the dependencies have been installed, generate the static asset bundle:

    a. If you're planning on editing HTML/CSS/JavaScript files, run `npm start`. This will start a development server that will automatically detect changes to static assets and rebuild the bundle.

    b. If you're not planning on editing HTML/CSS/JavaScript files, run `npm run build_development`

12. If you ran `npm start` in the previous step, you will need to open a new terminal window and activate the virtual environment in the new terminal window. If you ran `npm run build_development` then you can skip this step.

13. Setup the database:
    ```
    python manage.py setup_db
    ```

14. In the terminal window that is running the Django server, halt the server and restart it.
    ```
    (ctrl+c to halt the server)
    python manage.py runserver
    ```

## Committing changes

NOTE: Changes are committed to the arches-controlled-lists repository. 

1. Navigate to the repository
    ```
    cd arches-controlled-lists
    ```

2. Cut a new git branch
    ```
    git checkout origin/main -b my-descriptive-branch-name
    ```

3. If updating models or branches

    1. Manually export the model or branch from the project

    2. Manually move the exported model or branch into one of the subdirectories in the `arches-controlled-lists/arches_controlled_lists/pkg/graphs` directory.

4. Add your changes to the current git commit
    ```
    git status
    git add -- path/to/file path/to/second/file
    git commit -m "Descriptive commit message"
    ```

5. Update the remote repository with your commits:
    ```
    git push origin HEAD
    ```

6. Navigate to https://github.com/archesproject/arches-controlled-lists/pulls to see and commit the pull request
