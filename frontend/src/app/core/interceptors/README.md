# core/interceptors

Reserved for HTTP interceptors that are not tied to the API client
pipeline. The active interceptors for Phase 1 (`authInterceptor`,
`errorInterceptor`, `loadingInterceptor`) live in
[`core/http/`](../http/) alongside `ApiClientService`, since they are
registered together in `app.config.ts`. Add interceptors here instead once
a concern emerges that is independent of the API client (e.g. a
third-party analytics interceptor).
