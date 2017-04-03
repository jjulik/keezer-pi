drop table if exists token;
create table token (
	token text primary key,
	active integer not null
);

drop table if exists sensor;
create table sensor (
	sensorid integer primary key autoincrement,
	description text
);

drop table if exists reading;
create table reading (
	readingid integer primary key autoincrement,
	sensorid integer REFERENCES sensor(sensorid),
	[time] text not null,
	value text not null
);

