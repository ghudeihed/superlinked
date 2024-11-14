from superlinked.framework import (
    DataFormat,
    DataLoaderConfig,
    DataLoaderSource,
    IdField,
    Index,
    Integer,
    Mode,
    MongoDBVectorDatabase,
    NumberSpace,
    OpenAIClientConfig,
    Param,
    Query,
    RestDescriptor,
    RestExecutor,
    RestQuery,
    RestSource,
    String,
    SuperlinkedRegistry,
    TextSimilaritySpace,
    schema,
)

openai_config = OpenAIClientConfig(api_key="YOUR_OPENAI_API_KEY", model="gpt-4o")


@schema
class Review:
    id: IdField
    review_text: String
    rating: Integer
    full_review_as_text: String


review = Review()

review_text_space = TextSimilaritySpace(text=review.review_text, model="all-MiniLM-L6-v2")
rating_maximizer_space = NumberSpace(number=review.rating, min_value=1, max_value=5, mode=Mode.MAXIMUM)
full_review_as_text_space = TextSimilaritySpace(text=review.full_review_as_text, model="all-MiniLM-L6-v2")

naive_index = Index([full_review_as_text_space])
advanced_index = Index([review_text_space, rating_maximizer_space])

naive_query = (
    Query(
        naive_index,
        weights={full_review_as_text_space: Param("full_review_as_text_weight")},
    )
    .find(review)
    .similar(full_review_as_text_space.text, Param("query_text"))
    .limit(Param("limit"))
    .with_natural_query(Param("natural_query"), openai_config)
)
superlinked_query = (
    Query(
        advanced_index,
        weights={
            review_text_space: Param("review_text_weight"),
            rating_maximizer_space: Param("rating_maximizer_weight"),
        },
    )
    .find(review)
    .similar(review_text_space.text, Param("query_text"))
    .limit(Param("limit"))
    .with_natural_query(Param("natural_query"), openai_config)
)


review_source: RestSource = RestSource(review)
review_data_loader = DataLoaderConfig(
    "https://storage.googleapis.com/superlinked-sample-datasets/amazon_dataset_ext_1000.jsonl",
    DataFormat.JSON,
    pandas_read_kwargs={"lines": True, "chunksize": 100},
)
review_loader_source: DataLoaderSource = DataLoaderSource(review, review_data_loader)
mongo_db_vector_database = MongoDBVectorDatabase(
    "<USER>:<PASSWORD>@<HOST_URL>",
    "<DATABASE_NAME>",
    "<CLUSTER_NAME>",
    "<PROJECT_ID>",
    "<API_PUBLIC_KEY>",
    "<API_PRIVATE_KEY>",
)
executor = RestExecutor(
    sources=[review_source, review_loader_source],
    indices=[naive_index, advanced_index],
    queries=[
        RestQuery(RestDescriptor("naive_query"), naive_query),
        RestQuery(RestDescriptor("superlinked_query"), superlinked_query),
    ],
    vector_database=mongo_db_vector_database,
)

SuperlinkedRegistry.register(executor)
