
create table product_interest_requests (
  id uuid primary key default gen_random_uuid(),
  product_id bigint not null,
  product_title text not null,
  email text not null,
  created_at timestamptz default now()
);
