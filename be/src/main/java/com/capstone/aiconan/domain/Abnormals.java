package com.capstone.aiconan.domain;

import javax.persistence.*;

@Entity
@Inheritance(strategy = InheritanceType.SINGLE_TABLE)
@DiscriminatorColumn
public class Abnormals {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

}
