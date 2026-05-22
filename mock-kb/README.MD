# Mock GraphQL Document Service

## Description

This project is a mock GraphQL API built with FastAPI, Strawberry, and RapidFuzz. It provides pagination and fuzzy-search filtering for a preconfigured list of documents (stored in a local JSON file).

## How to Run

The project uses the `fastapi[standard]` package and `uv` for dependency management, you can run the development server using the built-in FastAPI CLI.

1. **Install dependencies:**
Make sure you have uv installed, then run the following command in the project root to sync your environment:

```shell
uv sync
```

2**Start the development server:**
Use uv run to execute the modern FastAPI standard CLI. This will automatically enable hot-reloading:

```shell
uv run fastapi dev
```

3. **Access the GraphiQL UI:**
Open your browser and navigate to the interactive GraphQL playground at:
http://localhost:8000/graphql

## API Description

The service exposes a single primary query: paginateDocuments.

**Query**: `paginateDocuments`

Fetches a list of documents based on optional search filters and pagination parameters. It performs a fuzzy search on both the title and text fields if a search string is provided.

**Arguments**

- `paginationParams` (Optional)

  - `offset` (Int): The starting index (default: 0).

  - `limit` (Int): The maximum number of documents to return (default: 10).

- `filterSettings` (Optional)

  - `searchString` (String): A term to fuzzy-match against document titles and texts.

  - `publicationDate` (Int - Timestamp): Exact timestamp match for the document's publication date.

**Returns**(`PaginatedDocuments)

- `total` (Int): The total number of documents matching the filters (ignoring pagination limits). Useful for building frontend pagination controls.

- `listDocument` (List of Document):

  - `id` (ID): Unique UUID of the document.

  - `title` (String): Document title.

  - `text` (String): Document body text.

  - `publicationDate` (Int): Unix timestamp of publication.

Example Query

```
query SearchAndPaginate {
  paginateDocuments(
    paginationParams: { offset: 0, limit: 5 },
    filterSettings: { searchString: "graphql" }
  ) {
    total
    listDocument {
      id
      title
      text
      publicationDate
    }
  }
}
```

## Data Configuration

The mock service loads its data from a local file named `documents.json` located in the root directory.

If this file does not exist when the server starts, the application will automatically generate a sample `documents.json` file to get you started.

To configure your own documents, simply edit or replace `documents.json`. The file must contain a JSON array of objects with the following strict structure:

```json

[
  {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "title": "Your Custom Document Title",
    "text": "The full text content of your document used for searching.",
    "publicationDate": 1683020000
  },
  {
    "id": "987fcdeb-51a2-43d7-9012-34567890abcd",
    "title": "Another Document",
    "text": "More content to be served by the API.",
    "publicationDate": 1714643100
  }
]
```


**Required Fields**

- `id` (String): A unique identifier for the document (UUIDs are recommended).

- `title` (String): The title of the document.

- `text` (String): The body content of the document.

- `publicationDate` (Integer): A Unix timestamp representing the publication date.

