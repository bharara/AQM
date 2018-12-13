DROP SCHEMA IF EXISTS sensor;
CREATE SCHEMA sensor;
USE sensor;


use sensor;

create table data (
	idData int auto_increment primary key not null,
    val1 int,
    val2 int);

create table classroom (
	classRoom varchar(30) primary key not null,
    openings int,
    floorplan int);
    
create table readings (
	classRoom varchar(30),
    startInstance int primary key,
    endInstance int,
    people int,
    foreign key(classRoom) references classroom(classRoom));
    
create table admins (
	adminName varchar(80) primary key,
    pword varchar(80) unique);
    
insert into classroom values ('CR8',3,2);
insert into admins values ('hadi','1234');