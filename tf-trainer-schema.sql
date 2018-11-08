create table posted_images
(
  image_id    int auto_increment
    primary key,
  year        int                                 null,
  make        varchar(55)                         null,
  model       varchar(55)                         null,
  url         varchar(65000)                      null,
  uploader_id int                                 null,
  processed   int                                 null,
  uploaded    timestamp default CURRENT_TIMESTAMP not null,
  json_data   text                                null
);

create table users
(
  user_id       int auto_increment
    primary key,
  username      varchar(55)                                    null,
  password      char(64)                                       null,
  session_token char(16)                                       null,
  last_login    timestamp default CURRENT_TIMESTAMP            not null
  on update CURRENT_TIMESTAMP,
  status        enum ('enabled', 'disabled') default 'enabled' null,
  constraint users_username_uindex
  unique (username)
);

