package com.capstone.aiconan.domain;

import javax.persistence.*;

@Entity(name = "abnormals")
@Inheritance(strategy = InheritanceType.SINGLE_TABLE)
@DiscriminatorColumn(name = "DTYPE")
public class Abnormal {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

}
