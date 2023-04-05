package com.capstone.aiconan.domain;

import lombok.AccessLevel;
import lombok.NoArgsConstructor;

import javax.persistence.*;

@Entity
@Table(name = "attack_types")
@NoArgsConstructor(access = AccessLevel.PROTECTED)
public class AttackType {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Enumerated(EnumType.STRING)
    private TypeOfAttack name;
}
